"""
Gemini Handler para interação com a API do Google Gemini.
Gerencia análise de casos clínicos e geração de diagnósticos diferenciais.
"""

import streamlit as st
import google.generativeai as genai
import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .logger import get_logger
from .validators import get_friendly_error_message


class GeminiHandler:
    """
    Gerencia interações com a API do Google Gemini para análise médica educacional.
    """
    
    def __init__(self):
        """
        Inicializa o handler e configura a API do Gemini.
        """
        self.model_name = "gemini-2.5-flash"
        self.model = None
        self.logger = get_logger()
        self._configure_api()
    
    def _configure_api(self) -> bool:
        """
        Configura a API do Gemini usando st.secrets.
        
        Returns:
            True se configuração foi bem-sucedida, False caso contrário
        """
        try:
            self.logger.info("Iniciando configuração da API Gemini")
            
            # Tentar obter API key do st.secrets
            if hasattr(st, 'secrets') and 'GEMINI_API_KEY' in st.secrets:
                api_key = st.secrets['GEMINI_API_KEY']
            else:
                self.logger.error("GEMINI_API_KEY não encontrada em st.secrets")
                st.error("⚠️ GEMINI_API_KEY não encontrada em st.secrets")
                return False
            
            # Configurar API
            genai.configure(api_key=api_key)
            
            # Inicializar modelo
            # Limite real do gemini-2.0-flash-exp: 65.536 tokens de saída
            # Usando ~50% do limite para balancear qualidade e custo
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 32768,  # ~50% do limite (65.536)
                }
            )
            
            self.logger.info(f"API Gemini configurada com sucesso. Modelo: {self.model_name}")
            return True
            
        except Exception as e:
            self.logger.error("Falha ao configurar API Gemini", error=e)
            error_msg = get_friendly_error_message(e)
            st.error(error_msg)
            return False
    
    def _create_diagnostic_prompt(self, context: str, specialty: str) -> str:
        """
        Cria o prompt estruturado para análise diagnóstica.
        
        Args:
            context: Contexto completo da consulta
            specialty: Especialidade médica selecionada
        
        Returns:
            Prompt formatado para o modelo
        """
        prompt = f"""Você é um assistente médico educacional especializado em {specialty}.

Sua função é auxiliar estudantes de medicina e profissionais em formação com análise de casos clínicos de forma EDUCACIONAL.

IMPORTANTE:
- Esta é uma ferramenta EDUCACIONAL, não para uso clínico real
- Forneça diagnósticos diferenciais baseados EXCLUSIVAMENTE nos dados apresentados
- Seja didático e explique o raciocínio clínico
- Atribua probabilidades realistas baseadas nas informações disponíveis
- Se houver dados insuficientes, indique isso claramente

DADOS DO CASO CLÍNICO:
{context}

ESPECIALIDADE: {specialty}

Por favor, analise este caso e forneça:

1. **Top 5 Diagnósticos Diferenciais** ranqueados por probabilidade
2. Para cada diagnóstico, forneça:
   - Nome do diagnóstico
   - Probabilidade estimada (0-100%) baseada APENAS nos dados apresentados
   - Justificativa clínica CONCISA (máximo 3-4 linhas)
   - 3-5 evidências a favor
   - 1-2 evidências contra
   - 2-3 dados clínicos principais

**IMPORTANTE PARA EVITAR TRUNCAMENTO:**
- Justificativas: máximo 250 caracteres cada
- Evidências: frases curtas e objetivas
- Observações: máximo 150 caracteres
- Dados insuficientes: lista breve

FORMATO DE RESPOSTA (retorne APENAS JSON válido, sem markdown):
{{
  "diagnosticos": [
    {{
      "nome": "Nome do Diagnóstico 1",
      "probabilidade": 75,
      "justificativa": "Explicação CONCISA do raciocínio clínico (max 250 chars)",
      "evidencias_favor": ["Evidência 1", "Evidência 2", "Evidência 3"],
      "evidencias_contra": ["Contra 1", "Contra 2"],
      "dados_principais": ["Dado 1", "Dado 2"]
    }},
    {{
      "nome": "Nome do Diagnóstico 2",
      "probabilidade": 60,
      "justificativa": "Explicação CONCISA (max 250 chars)",
      "evidencias_favor": ["..."],
      "evidencias_contra": ["..."],
      "dados_principais": ["..."]
    }}
  ],
  "observacoes": "Considerações importantes BREVES (max 150 chars)",
  "dados_insuficientes": ["Info faltante 1", "Info faltante 2"],
  "nivel_confianca": "alto/médio/baixo"
}}

Retorne SOMENTE o JSON, sem formatação markdown, sem ```json, apenas o objeto JSON puro.
SEJA CONCISO para evitar truncamento da resposta.
        
        return prompt
    
    def _parse_json_response(self, response_text: str) -> Optional[Dict]:
        """
        Parseia a resposta JSON do modelo, removendo markdown se necessário.
        Detecta e trata JSON truncado.
        
        Args:
            response_text: Texto da resposta do modelo
        
        Returns:
            Dicionário parseado ou None em caso de erro
        """
        try:
            # Remover possíveis marcadores de markdown
            clean_text = response_text.strip()
            
            # Remover ```json e ``` se presentes
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            elif clean_text.startswith("```"):
                clean_text = clean_text[3:]
            
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            
            clean_text = clean_text.strip()
            
            # Parsear JSON
            return json.loads(clean_text)
            
        except json.JSONDecodeError as e:
            error_msg = str(e)
            
            # Detectar JSON truncado (unterminated string/array/object)
            if "Unterminated" in error_msg or "Expecting" in error_msg:
                self.logger.warning(f"JSON truncado detectado: {error_msg}")
                st.warning(f"⚠️ **Resposta incompleta detectada**")
                st.info("""
                **O que aconteceu?**
                A resposta foi muito longa e foi cortada no meio.
                
                **Solução:**
                1. Clique em "Enviar e Analisar" novamente
                2. O sistema tentará gerar uma resposta mais concisa
                3. Se persistir, adicione informações aos poucos
                
                **Técnico:** JSON truncado - max_output_tokens atingido
                """)
                
                # Tentar salvar diagnósticos parciais se possível
                try:
                    # Tentar completar o JSON minimamente
                    if '"diagnosticos": [' in clean_text:
                        # Fechar arrays e objetos abertos
                        clean_text = clean_text.rstrip(',\n ')
                        # Contar abertura e fechamento
                        open_braces = clean_text.count('{')
                        close_braces = clean_text.count('}')
                        open_brackets = clean_text.count('[')
                        close_brackets = clean_text.count(']')
                        
                        # Adicionar fechamentos necessários
                        for _ in range(open_braces - close_braces):
                            clean_text += '\n}'
                        for _ in range(open_brackets - close_brackets):
                            clean_text += '\n]'
                        
                        # Tentar parsear novamente
                        partial_result = json.loads(clean_text)
                        
                        if 'diagnosticos' in partial_result and partial_result['diagnosticos']:
                            st.success(f"✅ Recuperados {len(partial_result['diagnosticos'])} diagnósticos parciais")
                            return partial_result
                except:
                    pass
            else:
                st.error(f"❌ Erro ao parsear resposta JSON: {error_msg}")
            
            # Mostrar JSON problemático em expander para debug
            with st.expander("🔍 Ver resposta problemática (Debug)", expanded=False):
                st.code(response_text[:3000] + "..." if len(response_text) > 3000 else response_text, language="text")
            
            return None
            
        except Exception as e:
            self.logger.error("Erro inesperado ao processar resposta", error=e)
            st.error(f"❌ Erro inesperado ao processar resposta: {str(e)}")
            return None
    
    def analyze_case(
        self,
        context: str,
        specialty: str,
        max_retries: int = 3
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Analisa um caso clínico e retorna diagnósticos diferenciais.
        
        Args:
            context: Contexto completo da consulta médica
            specialty: Especialidade médica selecionada
            max_retries: Número máximo de tentativas em caso de falha
        
        Returns:
            Tupla (resultado_dict, mensagem_erro)
            - resultado_dict: Dicionário com diagnósticos ou None em caso de erro
            - mensagem_erro: Mensagem de erro ou None se bem-sucedido
        """
        start_time = time.time()
        self.logger.info(f"Iniciando análise de caso", specialty=specialty, context_length=len(context))
        
        if not self.model:
            self.logger.error("Modelo Gemini não configurado")
            return None, "Modelo Gemini não está configurado corretamente"
        
        if not context or not context.strip():
            self.logger.warning("Contexto vazio fornecido para análise")
            return None, "Contexto vazio fornecido para análise"
        
        # Criar prompt
        prompt = self._create_diagnostic_prompt(context, specialty)
        
        # Tentar análise com retry logic
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Tentativa {attempt + 1}/{max_retries} de análise")
                
                # Enviar para o modelo
                response = self.model.generate_content(prompt)
                
                # Atualizar timestamp de última chamada à API (rate limiting)
                st.session_state.last_api_call = datetime.now()
                
                # Verificar se há resposta válida
                if not response or not response.text:
                    raise ValueError("Resposta vazia do modelo")
                
                # Parsear resposta JSON
                result = self._parse_json_response(response.text)
                
                if result:
                    # Validar estrutura básica
                    if "diagnosticos" in result and isinstance(result["diagnosticos"], list):
                        # Limitar a 5 diagnósticos
                        result["diagnosticos"] = result["diagnosticos"][:5]
                        
                        duration = time.time() - start_time
                        self.logger.log_api_call(
                            endpoint="analyze_case",
                            success=True,
                            duration=duration,
                            num_diagnostics=len(result["diagnosticos"])
                        )
                        
                        return result, None
                    else:
                        raise ValueError("Estrutura JSON inválida na resposta")
                
                # Se chegou aqui, parsing falhou
                if attempt < max_retries - 1:
                    self.logger.warning(f"Falha no parsing, tentando novamente em {2 ** attempt}s")
                    time.sleep(2 ** attempt)  # Backoff exponencial
                    continue
                else:
                    self.logger.error("Falha ao parsear resposta após múltiplas tentativas")
                    return None, "Falha ao parsear resposta após múltiplas tentativas"
                
            except Exception as e:
                self.logger.error(f"Erro na tentativa {attempt + 1}/{max_retries}", error=e)
                error_msg = get_friendly_error_message(e)
                
                if attempt < max_retries - 1:
                    st.warning(f"⚠️ {error_msg} Tentando novamente...")
                    time.sleep(2 ** attempt)  # Backoff exponencial: 1s, 2s, 4s
                else:
                    duration = time.time() - start_time
                    self.logger.log_api_call(
                        endpoint="analyze_case",
                        success=False,
                        duration=duration,
                        error=str(e)
                    )
                    return None, error_msg
        
        return None, "Erro desconhecido durante análise"
    
    def generate_suggestions(
        self,
        context: str,
        specialty: str,
        diagnosticos: Optional[List[Dict]] = None,
        max_retries: int = 2
    ) -> Optional[Dict]:
        """
        Gera sugestões de perguntas, exames e condutas baseadas no caso.
        Usa modelo gemini-2.5-flash para respostas mais rápidas.
        
        Args:
            context: Contexto da consulta
            specialty: Especialidade médica
            diagnosticos: Lista opcional de diagnósticos diferenciais
            max_retries: Número máximo de tentativas
        
        Returns:
            Dicionário com sugestões ou None em caso de erro
            Formato: {
                "follow_up_questions": [...],
                "suggested_exams": [...],
                "management_suggestions": [...]
            }
        """
        start_time = time.time()
        self.logger.info("Iniciando geração de sugestões", specialty=specialty)
        
        try:
            # Criar modelo específico para sugestões (mais rápido)
            suggestions_model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",  # Modelo mais rápido para sugestões
                generation_config={
                    "temperature": 0.8,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,  # Aumentado para sugestões mais completas
                }
            )
            
            # Criar contexto adicional se houver diagnósticos
            diagnosticos_context = ""
            if diagnosticos and len(diagnosticos) > 0:
                diagnosticos_str = "\n".join([
                    f"- {d.get('nome', 'N/A')} ({d.get('probabilidade', 0)}%)"
                    for d in diagnosticos[:3]
                ])
                diagnosticos_context = f"""

PRINCIPAIS HIPÓTESES DIAGNÓSTICAS CONSIDERADAS:
{diagnosticos_str}"""
            
            prompt = f"""Você é um assistente médico educacional especializado em {specialty}.

Com base no caso clínico abaixo, forneça sugestões práticas e educacionais para auxiliar o estudante na condução adequada do caso.

DADOS DO CASO:
{context}{diagnosticos_context}

Forneça:

1. **PERGUNTAS DE SEGUIMENTO**: 3-5 perguntas ESSENCIAIS e específicas a fazer ao paciente para complementar a anamnese e ajudar no diagnóstico diferencial. Seja objetivo e prático.

2. **EXAMES COMPLEMENTARES**: 3-5 exames laboratoriais, de imagem ou outros que sejam PERTINENTES e prioritários para este caso específico. Liste do mais urgente/importante para o menos.

3. **SUGESTÕES DE CONDUTA**: 3-5 recomendações de manejo clínico BASEADAS NOS DADOS ATUAIS. Inclua medidas iniciais, estabilização, tratamentos sintomáticos ou específicos, quando encaminhar, etc.

IMPORTANTE:
- Seja específico e relevante para ESTE caso
- Priorize por importância clínica
- Considere a especialidade de {specialty}
- Seja educacional mas prático

FORMATO DE RESPOSTA (retorne APENAS JSON válido, sem markdown):
{{
  "follow_up_questions": [
    "Pergunta específica 1",
    "Pergunta específica 2",
    "Pergunta específica 3"
  ],
  "suggested_exams": [
    "Exame prioritário 1",
    "Exame prioritário 2",
    "Exame prioritário 3"
  ],
  "management_suggestions": [
    "Conduta/manejo 1",
    "Conduta/manejo 2",
    "Conduta/manejo 3"
  ]
}}

Retorne SOMENTE o objeto JSON, sem formatação markdown."""
            
            # Tentar gerar sugestões com retry
            for attempt in range(max_retries):
                try:
                    self.logger.debug(f"Tentativa {attempt + 1}/{max_retries} de gerar sugestões")
                    response = suggestions_model.generate_content(prompt)
                    
                    # Atualizar timestamp de última chamada à API
                    st.session_state.last_api_call = datetime.now()
                    
                    if response and response.text:
                        result = self._parse_json_response(response.text)
                        
                        if result and self._validate_suggestions_structure(result):
                            duration = time.time() - start_time
                            self.logger.log_api_call(
                                endpoint="generate_suggestions",
                                success=True,
                                duration=duration
                            )
                            return result
                        else:
                            if attempt < max_retries - 1:
                                self.logger.warning("Falha na validação de sugestões, tentando novamente")
                                time.sleep(1)
                                continue
                    
                except Exception as e:
                    self.logger.error(f"Erro na tentativa {attempt + 1}/{max_retries} de gerar sugestões", error=e)
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        error_msg = get_friendly_error_message(e)
                        st.warning(f"⚠️ {error_msg}")
                        return None
            
            self.logger.warning("Todas as tentativas de gerar sugestões falharam")
            return None
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_api_call(
                endpoint="generate_suggestions",
                success=False,
                duration=duration,
                error=str(e)
            )
            error_msg = get_friendly_error_message(e)
            st.error(error_msg)
            return None
    
    def _validate_suggestions_structure(self, data: Dict) -> bool:
        """
        Valida estrutura do JSON de sugestões.
        
        Args:
            data: Dicionário a validar
        
        Returns:
            True se válido, False caso contrário
        """
        required_keys = ["follow_up_questions", "suggested_exams", "management_suggestions"]
        
        if not all(key in data for key in required_keys):
            return False
        
        # Verificar se são listas
        for key in required_keys:
            if not isinstance(data[key], list):
                return False
        
        return True
    
    def generate_medical_record(
        self,
        context: str,
        diagnosticos: List[Dict],
        format_type: str = "Tradicional"
    ) -> Optional[str]:
        """
        Gera prontuário médico formatado.
        
        Args:
            context: Contexto da consulta
            diagnosticos: Lista de diagnósticos
            format_type: "Tradicional" ou "SOAP"
        
        Returns:
            Texto do prontuário formatado ou None em caso de erro
        """
        start_time = time.time()
        self.logger.info(f"Iniciando geração de prontuário", format_type=format_type)
        
        if not self.model:
            self.logger.error("Modelo Gemini não configurado")
            return None
        
        diagnosticos_str = "\n".join([
            f"{i+1}. {d['nome']} - {d['probabilidade']}%"
            for i, d in enumerate(diagnosticos[:5])
        ])
        
        if format_type == "SOAP":
            prompt_format = """formato SOAP (Subjetivo, Objetivo, Avaliação, Plano):

S (SUBJETIVO): Queixa principal e história
O (OBJETIVO): Exame físico e dados objetivos
A (AVALIAÇÃO): Hipóteses diagnósticas e raciocínio
P (PLANO): Condutas e exames propostos"""
        else:
            prompt_format = """formato TRADICIONAL:

- Identificação do paciente
- Queixa principal
- História da doença atual
- Antecedentes
- Exame físico
- Hipóteses diagnósticas
- Plano"""
        
        prompt = f"""Crie um prontuário médico EDUCACIONAL em {prompt_format}

DADOS DO CASO:
{context}

HIPÓTESES DIAGNÓSTICAS:
{diagnosticos_str}

Gere um prontuário bem estruturado e didático para fins educacionais.
Retorne o texto formatado do prontuário."""
        
        try:
            self.logger.debug("Enviando requisição para gerar prontuário")
            response = self.model.generate_content(prompt)
            
            # Atualizar timestamp de última chamada à API
            st.session_state.last_api_call = datetime.now()
            
            if response and response.text:
                duration = time.time() - start_time
                self.logger.log_api_call(
                    endpoint="generate_medical_record",
                    success=True,
                    duration=duration,
                    format_type=format_type
                )
                return response.text.strip()
            
            self.logger.warning("Resposta vazia ao gerar prontuário")
            return None
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_api_call(
                endpoint="generate_medical_record",
                success=False,
                duration=duration,
                error=str(e)
            )
            error_msg = get_friendly_error_message(e)
            st.error(error_msg)
            return None


# Funções utilitárias para uso direto

def analyze_case(context: str, specialty: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Função auxiliar para análise de caso.
    
    Args:
        context: Contexto completo da consulta
        specialty: Especialidade médica
    
    Returns:
        Tupla (resultado, erro)
    """
    handler = GeminiHandler()
    return handler.analyze_case(context, specialty)


def get_gemini_handler() -> GeminiHandler:
    """
    Retorna uma instância singleton do GeminiHandler.
    
    Returns:
        Instância do GeminiHandler
    """
    if 'gemini_handler' not in st.session_state:
        st.session_state.gemini_handler = GeminiHandler()
    
    return st.session_state.gemini_handler

