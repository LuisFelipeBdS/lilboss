"""
Validators - Validações e verificações de segurança.

Este módulo contém funções para validar API keys, contexto e outros requisitos.
"""

import streamlit as st
import google.generativeai as genai
from typing import Tuple, Optional
import re


def validate_gemini_api_key() -> Tuple[bool, Optional[str]]:
    """
    Valida se a API key do Gemini está configurada e é válida.
    
    Returns:
        Tupla (is_valid: bool, error_message: str)
    """
    # Verificar se existe no secrets
    if not hasattr(st, 'secrets'):
        return False, "Arquivo secrets.toml não encontrado"
    
    if 'GEMINI_API_KEY' not in st.secrets:
        return False, "GEMINI_API_KEY não está configurada em secrets.toml"
    
    api_key = st.secrets['GEMINI_API_KEY']
    
    # Verificar se não está vazia
    if not api_key or not api_key.strip():
        return False, "GEMINI_API_KEY está vazia"
    
    # Verificar formato básico (começa com AIza ou outras variações do Google)
    if not (api_key.startswith('AIza') or len(api_key) > 30):
        return False, "GEMINI_API_KEY parece ter formato inválido"
    
    # Tentar configurar e fazer teste simples
    try:
        genai.configure(api_key=api_key)
        
        # Tentar listar modelos como teste
        list(genai.list_models())
        
        return True, None
        
    except Exception as e:
        error_msg = str(e)
        
        if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
            return False, "API key inválida. Verifique se está correta."
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            return False, "Limite de uso da API excedido. Aguarde ou use outra key."
        elif "permission" in error_msg.lower():
            return False, "Permissão negada. Verifique se a API está habilitada."
        else:
            return False, f"Erro ao validar API key: {error_msg}"


def validate_context_for_analysis(context: str, min_chars: int = 50) -> Tuple[bool, Optional[str]]:
    """
    Valida se há contexto suficiente para análise.
    
    Args:
        context: Texto do contexto
        min_chars: Número mínimo de caracteres
    
    Returns:
        Tupla (is_valid: bool, error_message: str)
    """
    if not context or not context.strip():
        return False, "Nenhum dado foi fornecido para análise"
    
    context_clean = context.strip()
    
    if len(context_clean) < min_chars:
        return False, f"Contexto muito curto (mínimo {min_chars} caracteres). Forneça mais informações sobre o caso."
    
    # Verificar se tem pelo menos algumas palavras
    words = context_clean.split()
    if len(words) < 10:
        return False, "Forneça mais detalhes sobre o caso clínico (mínimo 10 palavras)."
    
    # Verificar se não é só números ou caracteres especiais
    alpha_chars = sum(c.isalpha() for c in context_clean)
    if alpha_chars < min_chars / 2:
        return False, "O contexto deve conter texto descritivo, não apenas números."
    
    return True, None


def validate_diagnosticos(diagnosticos: list) -> Tuple[bool, Optional[str]]:
    """
    Valida estrutura da lista de diagnósticos.
    
    Args:
        diagnosticos: Lista de diagnósticos
    
    Returns:
        Tupla (is_valid: bool, error_message: str)
    """
    if not diagnosticos:
        return False, "Nenhum diagnóstico fornecido"
    
    if not isinstance(diagnosticos, list):
        return False, "Diagnósticos devem ser uma lista"
    
    for idx, diag in enumerate(diagnosticos):
        if not isinstance(diag, dict):
            return False, f"Diagnóstico {idx+1} não é um dicionário válido"
        
        if 'nome' not in diag:
            return False, f"Diagnóstico {idx+1} não tem campo 'nome'"
        
        if 'probabilidade' not in diag:
            return False, f"Diagnóstico {idx+1} não tem campo 'probabilidade'"
        
        # Validar probabilidade
        prob = diag.get('probabilidade', 0)
        if not isinstance(prob, (int, float)):
            return False, f"Probabilidade do diagnóstico {idx+1} deve ser numérica"
        
        if prob < 0 or prob > 100:
            return False, f"Probabilidade do diagnóstico {idx+1} deve estar entre 0 e 100"
    
    return True, None


def check_minimum_data_for_prontuario(context: str) -> Tuple[bool, Optional[str]]:
    """
    Verifica se há dados mínimos para gerar prontuário.
    
    Args:
        context: Contexto do caso
    
    Returns:
        Tupla (is_valid: bool, error_message: str)
    """
    if not context or len(context.strip()) < 100:
        return False, "Dados insuficientes para gerar prontuário. Adicione mais informações sobre o caso."
    
    context_lower = context.lower()
    
    # Verificar se tem pelo menos alguns elementos básicos
    has_patient_info = any(word in context_lower for word in ['paciente', 'anos', 'idade', 'sexo', 'masculino', 'feminino'])
    has_complaint = any(word in context_lower for word in ['queixa', 'dor', 'febre', 'sintoma', 'refere', 'relata'])
    
    if not has_patient_info:
        return False, "Adicione informações básicas do paciente (idade, sexo) para gerar o prontuário."
    
    if not has_complaint:
        return False, "Adicione a queixa principal ou sintomas do paciente para gerar o prontuário."
    
    return True, None


def sanitize_input(text: str, max_length: int = 50000) -> str:
    """
    Sanitiza input do usuário.
    
    Args:
        text: Texto a sanitizar
        max_length: Tamanho máximo permitido
    
    Returns:
        Texto sanitizado
    """
    if not text:
        return ""
    
    # Remover espaços extras
    text = " ".join(text.split())
    
    # Limitar tamanho
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remover caracteres de controle perigosos (manter quebras de linha)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    return text


def validate_specialty(specialty: str) -> Tuple[bool, Optional[str]]:
    """
    Valida se a especialidade é válida.
    
    Args:
        specialty: Nome da especialidade
    
    Returns:
        Tupla (is_valid: bool, error_message: str)
    """
    valid_specialties = [
        "Clínica Médica",
        "Cardiologia",
        "Pneumologia",
        "Gastroenterologia",
        "Neurologia",
        "Pediatria",
        "Ginecologia/Obstetrícia",
        "Outros"
    ]
    
    if not specialty:
        return False, "Especialidade não selecionada"
    
    if specialty not in valid_specialties:
        return False, f"Especialidade '{specialty}' não é válida"
    
    return True, None


def get_validation_summary() -> dict:
    """
    Retorna resumo de todas as validações do sistema.
    
    Returns:
        Dicionário com status das validações
    """
    summary = {
        'api_key_valid': False,
        'api_key_error': None,
        'system_ready': False
    }
    
    # Validar API key
    api_valid, api_error = validate_gemini_api_key()
    summary['api_key_valid'] = api_valid
    summary['api_key_error'] = api_error
    
    # Sistema pronto se API key válida
    summary['system_ready'] = api_valid
    
    return summary


# Funções de helper para mensagens de erro amigáveis

def get_friendly_error_message(error: Exception) -> str:
    """
    Converte exceção em mensagem amigável.
    
    Args:
        error: Exceção capturada
    
    Returns:
        Mensagem amigável para o usuário
    """
    error_str = str(error).lower()
    
    # Erros de API
    if "api_key_invalid" in error_str or "invalid api key" in error_str:
        return "❌ API key inválida. Verifique sua configuração em .streamlit/secrets.toml"
    
    if "quota" in error_str or "limit exceeded" in error_str:
        return "⏱️ Limite de uso da API excedido. Aguarde alguns minutos ou use outra API key."
    
    if "rate limit" in error_str:
        return "🚦 Muitas requisições em pouco tempo. Aguarde alguns segundos e tente novamente."
    
    if "timeout" in error_str:
        return "⌛ Tempo de resposta excedido. Tente novamente."
    
    if "connection" in error_str or "network" in error_str:
        return "🌐 Erro de conexão com a API. Verifique sua internet e tente novamente."
    
    if "permission" in error_str or "forbidden" in error_str:
        return "🔒 Permissão negada. Verifique se a API Gemini está habilitada no seu projeto."
    
    if "not found" in error_str:
        return "🔍 Recurso não encontrado. Verifique se o modelo está disponível."
    
    if "invalid argument" in error_str or "invalid request" in error_str:
        return "⚠️ Requisição inválida. Verifique os dados fornecidos."
    
    # Erro genérico
    return f"❌ Erro inesperado: {str(error)[:100]}"


def check_rate_limit_status() -> Tuple[bool, Optional[str]]:
    """
    Verifica status de rate limiting.
    
    Returns:
        Tupla (can_proceed: bool, message: str)
    """
    # Verificar última chamada
    if 'last_api_call' in st.session_state and st.session_state.last_api_call:
        from datetime import datetime, timedelta
        
        time_since_last = datetime.now() - st.session_state.last_api_call
        
        if time_since_last.total_seconds() < 3:
            remaining = 3 - int(time_since_last.total_seconds())
            return False, f"⏱️ Aguarde {remaining} segundo(s) antes da próxima análise (rate limiting)"
    
    return True, None

