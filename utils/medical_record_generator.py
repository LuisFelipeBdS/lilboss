"""
Medical Record Generator - Gerador de Prontuários Médicos.

Este módulo contém funções para gerar prontuários médicos em formatos
Tradicional e SOAP utilizando o Google Gemini.
"""

import streamlit as st
import google.generativeai as genai
from typing import Optional, Tuple
import time
from datetime import datetime
from .logger import get_logger
from .validators import get_friendly_error_message


class MedicalRecordGenerator:
    """
    Gerenciador de geração de prontuários médicos em diferentes formatos.
    """
    
    def __init__(self):
        """
        Inicializa o gerador de prontuários.
        """
        self.model_name = "gemini-2.5-pro"
        self.model = None
        self.logger = get_logger()
        self._configure_api()
    
    def _configure_api(self) -> bool:
        """
        Configura a API do Gemini.
        
        Returns:
            True se configuração bem-sucedida, False caso contrário
        """
        try:
            self.logger.info(f"Configurando API para geração de prontuários. Modelo: {self.model_name}")
            
            if hasattr(st, 'secrets') and 'GEMINI_API_KEY' in st.secrets:
                api_key = st.secrets['GEMINI_API_KEY']
                genai.configure(api_key=api_key)
                
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config={
                        "temperature": 0.3,  # Mais conservador para prontuários
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 8192,
                    }
                )
                self.logger.info("API configurada com sucesso para prontuários")
                return True
            else:
                self.logger.error("GEMINI_API_KEY não encontrada em secrets")
                return False
        except Exception as e:
            self.logger.error("Erro ao configurar API para prontuários", error=e)
            error_msg = get_friendly_error_message(e)
            st.error(error_msg)
            return False
    
    def generate_traditional_record(
        self,
        context: str,
        diagnosticos: Optional[list] = None,
        max_retries: int = 2
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Gera prontuário médico no formato tradicional brasileiro.
        
        Args:
            context: Contexto completo da consulta
            diagnosticos: Lista opcional de diagnósticos
            max_retries: Número máximo de tentativas
        
        Returns:
            Tupla (prontuário_texto, mensagem_erro)
        """
        start_time = time.time()
        self.logger.info("Iniciando geração de prontuário tradicional", context_length=len(context))
        
        if not self.model:
            self.logger.error("Modelo não configurado para gerar prontuário")
            return None, "Modelo Gemini não configurado"
        
        # Criar contexto de diagnósticos se disponível
        diagnosticos_text = ""
        if diagnosticos and len(diagnosticos) > 0:
            diagnosticos_text = "\n\n**HIPÓTESES DIAGNÓSTICAS GERADAS:**\n"
            for idx, diag in enumerate(diagnosticos[:5], 1):
                diagnosticos_text += f"{idx}. {diag.get('nome', 'N/A')} - {diag.get('probabilidade', 0)}%\n"
        
        prompt = f"""Você é um médico experiente criando um prontuário médico educacional no formato TRADICIONAL brasileiro.

**IMPORTANTE:**
- Este é um prontuário EDUCACIONAL para fins de ensino
- Organize as informações do caso nos campos apropriados
- Mantenha linguagem técnica médica adequada
- Inclua TODOS os dados relevantes fornecidos
- Use formato Markdown para melhor legibilidade
- Se alguma informação não estiver disponível, escreva "Não informado" ou "Não avaliado"

**DADOS DO CASO CLÍNICO:**
{context}
{diagnosticos_text}

**ESTRUTURA DO PRONTUÁRIO TRADICIONAL BRASILEIRO:**

## 📋 IDENTIFICAÇÃO
- Nome: [Se não informado, use "Paciente"]
- Idade e Sexo: [Extrair dos dados]
- Data da Consulta: {datetime.now().strftime("%d/%m/%Y")}
- Profissão: [Se informado]
- Naturalidade/Procedência: [Se informado]

## 🗣️ QUEIXA PRINCIPAL (QP)
[Sintoma ou motivo principal que levou o paciente a procurar atendimento - em uma frase curta]

## 📖 HISTÓRIA DA DOENÇA ATUAL (HDA)
[Descrição cronológica e detalhada dos sintomas atuais, incluindo:
- Início dos sintomas (quando começou)
- Características (tipo, intensidade, localização)
- Evolução (melhora, piora, estável)
- Fatores de melhora ou piora
- Sintomas associados
- Tratamentos já realizados]

## 🔍 REVISÃO DE SISTEMAS
[Investigação de sintomas por sistemas - mencionar apenas se informado:
- Geral: febre, perda de peso, astenia
- Cardiovascular: palpitações, dispneia, edema
- Respiratório: tosse, dispneia, dor torácica
- Gastrointestinal: náuseas, vômitos, diarreia, constipação
- Geniturinário: disúria, hematúria, alterações urinárias
- Neurológico: cefaleia, tonturas, alterações sensitivas
- Outros sistemas relevantes]

## 🏥 HISTÓRIA PATOLÓGICA PREGRESSA (HPP)
[Doenças anteriores, cirurgias, internações, alergias, medicações em uso]

## 👨‍👩‍👧‍👦 HISTÓRIA FAMILIAR (HF)
[Doenças relevantes em familiares de primeiro grau]

## 🚬 HISTÓRIA SOCIAL E HÁBITOS DE VIDA (HS)
[Tabagismo, etilismo, uso de drogas, atividade física, alimentação, condições de moradia]

## 🔬 EXAMES COMPLEMENTARES
[Resultados de exames laboratoriais, de imagem ou outros procedimentos - se disponíveis]

## 🩺 EXAME FÍSICO (EF)
### Estado Geral
[Aspecto geral do paciente]

### Sinais Vitais
[PA, FC, FR, Temperatura, Sat O2 - se informados]

### Exame Físico Segmentar
[Detalhar os achados por sistemas/segmentos examinados]

## 💭 IMPRESSÕES DIAGNÓSTICAS
[Liste as hipóteses diagnósticas em ordem de probabilidade, baseadas nos dados apresentados]

## 📝 CONDUTA
[Plano terapêutico proposto, exames solicitados, orientações, encaminhamentos]

---
*Prontuário gerado para fins educacionais - {datetime.now().strftime("%d/%m/%Y às %H:%M")}*

**IMPORTANTE:** Forneça um prontuário completo e bem estruturado usando APENAS as informações disponíveis no contexto fornecido. Para campos sem informação, indique claramente "Não informado" ou "Não avaliado".

Retorne APENAS o prontuário formatado em Markdown, sem comentários adicionais."""
        
        # Tentar gerar com retry
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Tentativa {attempt + 1}/{max_retries} de gerar prontuário tradicional")
                response = self.model.generate_content(prompt)
                
                # Atualizar timestamp de última chamada à API
                st.session_state.last_api_call = datetime.now()
                
                if response and response.text:
                    duration = time.time() - start_time
                    self.logger.log_api_call(
                        endpoint="generate_traditional_record",
                        success=True,
                        duration=duration,
                        num_diagnostics=len(diagnosticos) if diagnosticos else 0
                    )
                    return response.text.strip(), None
                else:
                    if attempt < max_retries - 1:
                        self.logger.warning("Resposta vazia, tentando novamente")
                        time.sleep(1)
                        continue
                    self.logger.error("Resposta vazia após todas as tentativas")
                    return None, "Resposta vazia do modelo"
                    
            except Exception as e:
                self.logger.error(f"Erro na tentativa {attempt + 1}/{max_retries}", error=e)
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    duration = time.time() - start_time
                    self.logger.log_api_call(
                        endpoint="generate_traditional_record",
                        success=False,
                        duration=duration,
                        error=str(e)
                    )
                    error_msg = get_friendly_error_message(e)
                    return None, error_msg
        
        return None, "Erro desconhecido"
    
    def generate_soap_record(
        self,
        context: str,
        diagnosticos: Optional[list] = None,
        max_retries: int = 2
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Gera prontuário médico no formato SOAP.
        
        Args:
            context: Contexto completo da consulta
            diagnosticos: Lista opcional de diagnósticos
            max_retries: Número máximo de tentativas
        
        Returns:
            Tupla (prontuário_texto, mensagem_erro)
        """
        start_time = time.time()
        self.logger.info("Iniciando geração de prontuário SOAP", context_length=len(context))
        
        if not self.model:
            self.logger.error("Modelo não configurado para gerar prontuário")
            return None, "Modelo Gemini não configurado"
        
        # Criar contexto de diagnósticos se disponível
        diagnosticos_text = ""
        if diagnosticos and len(diagnosticos) > 0:
            diagnosticos_text = "\n\n**HIPÓTESES DIAGNÓSTICAS GERADAS:**\n"
            for idx, diag in enumerate(diagnosticos[:5], 1):
                diagnosticos_text += f"{idx}. {diag.get('nome', 'N/A')} - {diag.get('probabilidade', 0)}%\n"
        
        prompt = f"""Você é um médico experiente criando um prontuário médico educacional no formato SOAP (Subjetivo, Objetivo, Avaliação, Plano).

**IMPORTANTE:**
- Este é um prontuário EDUCACIONAL para fins de ensino
- Organize as informações do caso na estrutura SOAP
- Mantenha linguagem técnica médica adequada
- Inclua TODOS os dados relevantes fornecidos
- Use formato Markdown para melhor legibilidade
- Seja conciso mas completo

**DADOS DO CASO CLÍNICO:**
{context}
{diagnosticos_text}

**ESTRUTURA DO PRONTUÁRIO SOAP:**

## 📋 IDENTIFICAÇÃO
- Paciente: [Idade, sexo, profissão se informado]
- Data: {datetime.now().strftime("%d/%m/%Y às %H:%M")}

---

## 🗣️ S - SUBJETIVO
**[Informações RELATADAS pelo paciente]**

### Queixa Principal (QP)
[Motivo da consulta na voz do paciente]

### História da Doença Atual (HDA)
[Narrativa do paciente sobre seus sintomas:
- O que está sentindo
- Quando começou
- Como evoluiu
- O que melhora ou piora
- Sintomas associados que relata]

### História Pregressa
[Doenças anteriores, cirurgias, alergias, medicações em uso - conforme relatado]

### História Familiar
[Doenças em familiares - se relatado]

### História Social
[Hábitos de vida, profissão, condições sociais - se relatado]

---

## 🔍 O - OBJETIVO  
**[Dados CONCRETOS e MENSURÁVEIS observados]**

### Sinais Vitais
[Medidas objetivas: PA, FC, FR, Temperatura, Sat O2, etc.]

### Exame Físico
[Achados do exame físico segmentar:
- Estado geral
- Aspectos específicos observados
- Auscultas
- Palpações
- Inspeção
- Outros achados objetivos]

### Exames Complementares
[Resultados de exames laboratoriais, imagem, ECG, etc. - se disponíveis]

---

## 💭 A - AVALIAÇÃO (Análise)
**[INTERPRETAÇÃO clínica dos dados]**

### Síntese do Caso
[Resumo integrado das informações subjetivas e objetivas]

### Hipóteses Diagnósticas
[Lista de diagnósticos diferenciais em ordem de probabilidade:
1. Diagnóstico mais provável - Justificativa
2. Segunda hipótese - Justificativa
3. Terceira hipótese - Justificativa
...]

### Raciocínio Clínico
[Explicação de como os dados levam às hipóteses diagnósticas]

---

## 📝 P - PLANO
**[CONDUTAS e ações propostas]**

### Tratamento
[Medicações, doses, vias, duração]

### Exames Solicitados
[Exames complementares necessários]

### Orientações
[Recomendações ao paciente]

### Retorno/Seguimento
[Quando retornar, sinais de alerta]

### Encaminhamentos
[Se necessário, para qual especialidade]

---
*Prontuário SOAP gerado para fins educacionais - {datetime.now().strftime("%d/%m/%Y às %H:%M")}*

**IMPORTANTE:** Forneça um prontuário SOAP completo e bem estruturado usando APENAS as informações disponíveis no contexto fornecido. Seja objetivo e técnico.

Retorne APENAS o prontuário formatado em Markdown, sem comentários adicionais."""
        
        # Tentar gerar com retry
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Tentativa {attempt + 1}/{max_retries} de gerar prontuário SOAP")
                response = self.model.generate_content(prompt)
                
                # Atualizar timestamp de última chamada à API
                st.session_state.last_api_call = datetime.now()
                
                if response and response.text:
                    duration = time.time() - start_time
                    self.logger.log_api_call(
                        endpoint="generate_soap_record",
                        success=True,
                        duration=duration,
                        num_diagnostics=len(diagnosticos) if diagnosticos else 0
                    )
                    return response.text.strip(), None
                else:
                    if attempt < max_retries - 1:
                        self.logger.warning("Resposta vazia, tentando novamente")
                        time.sleep(1)
                        continue
                    self.logger.error("Resposta vazia após todas as tentativas")
                    return None, "Resposta vazia do modelo"
                    
            except Exception as e:
                self.logger.error(f"Erro na tentativa {attempt + 1}/{max_retries}", error=e)
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    duration = time.time() - start_time
                    self.logger.log_api_call(
                        endpoint="generate_soap_record",
                        success=False,
                        duration=duration,
                        error=str(e)
                    )
                    error_msg = get_friendly_error_message(e)
                    return None, error_msg
        
        return None, "Erro desconhecido"


# Funções auxiliares para facilitar uso

def generate_traditional_record(
    context: str,
    diagnosticos: Optional[list] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Função auxiliar para gerar prontuário tradicional.
    
    Args:
        context: Contexto da consulta
        diagnosticos: Lista opcional de diagnósticos
    
    Returns:
        Tupla (prontuário, erro)
    """
    generator = MedicalRecordGenerator()
    return generator.generate_traditional_record(context, diagnosticos)


def generate_soap_record(
    context: str,
    diagnosticos: Optional[list] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Função auxiliar para gerar prontuário SOAP.
    
    Args:
        context: Contexto da consulta
        diagnosticos: Lista opcional de diagnósticos
    
    Returns:
        Tupla (prontuário, erro)
    """
    generator = MedicalRecordGenerator()
    return generator.generate_soap_record(context, diagnosticos)


def get_medical_record_generator():
    """
    Retorna instância singleton do gerador de prontuários.
    
    Returns:
        Instância de MedicalRecordGenerator
    """
    if 'medical_record_generator' not in st.session_state:
        st.session_state.medical_record_generator = MedicalRecordGenerator()
    
    return st.session_state.medical_record_generator

