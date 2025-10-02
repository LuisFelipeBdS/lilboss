import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime, timedelta
from utils import (
    get_gemini_handler,
    ContextManager,
    get_medical_record_generator,
    validate_gemini_api_key,
    validate_context_for_analysis,
    check_minimum_data_for_prontuario,
    get_friendly_error_message,
    check_rate_limit_status,
    get_logger,
    log_session_info,
    log_exception,
    log_performance_metric
)

# Configuração da página
st.set_page_config(
    page_title="Assistente de Consulta Médica - Estudante",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS CUSTOMIZADO ====================
def apply_custom_css():
    """Aplica CSS customizado com tema médico profissional."""
    st.markdown("""
    <style>
    /* Tema Principal - Cores Médicas */
    :root {
        --primary-color: #0066CC;
        --secondary-color: #00A86B;
        --accent-color: #1E90FF;
        --bg-light: #F8F9FA;
        --bg-card: #FFFFFF;
        --text-primary: #2C3E50;
        --text-secondary: #546E7A;
        --border-color: #E0E0E0;
        --success-color: #28A745;
        --warning-color: #FFC107;
        --danger-color: #DC3545;
        --info-color: #17A2B8;
    }
    
    /* Estilo Global */
    .main {
        background-color: var(--bg-light);
    }
    
    /* Títulos e Headers */
    h1 {
        color: var(--primary-color) !important;
        font-weight: 700 !important;
        border-bottom: 3px solid var(--secondary-color);
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    h2 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        margin-top: 20px;
    }
    
    h3 {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
    }
    
    /* Cards e Containers */
    .stExpander {
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    
    /* Botões */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Botões Primários (tipo primary) */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
    }
    
    /* Botões Secundários */
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, var(--secondary-color) 0%, #00C97F 100%);
    }
    
    /* TextArea e Input */
    .stTextArea textarea {
        border: 2px solid var(--border-color);
        border-radius: 8px;
        font-size: 14px;
        transition: border-color 0.3s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.1);
    }
    
    /* SelectBox */
    .stSelectbox {
        border-radius: 6px;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: var(--primary-color);
        font-size: 24px;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary);
        font-weight: 500;
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--secondary-color) 0%, var(--primary-color) 100%);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFFFFF 0%, var(--bg-light) 100%);
        border-right: 2px solid var(--border-color);
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: var(--primary-color) !important;
    }
    
    /* Alertas Customizados */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid;
        padding: 12px 16px;
    }
    
    /* Tooltips */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
        color: var(--info-color);
        margin-left: 5px;
    }
    
    .tooltip:hover::after {
        content: attr(data-tooltip);
        position: absolute;
        background-color: var(--text-primary);
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        white-space: nowrap;
        z-index: 1000;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    /* Cards de Diagnóstico */
    .diagnostic-card {
        background: var(--bg-card);
        border-left: 4px solid var(--primary-color);
        border-radius: 8px;
        padding: 16px;
        margin: 10px 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        transition: transform 0.2s ease;
    }
    
    .diagnostic-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    
    /* Badge de Probabilidade */
    .probability-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 12px;
        margin-left: 10px;
    }
    
    .prob-high {
        background-color: #FEE;
        color: var(--danger-color);
    }
    
    .prob-medium {
        background-color: #FFF3CD;
        color: #856404;
    }
    
    .prob-low {
        background-color: #D1ECF1;
        color: #0C5460;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        h1 {
            font-size: 24px !important;
        }
        
        h2 {
            font-size: 20px !important;
        }
        
        .stButton > button {
            font-size: 14px;
            padding: 8px 16px;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 18px;
        }
    }
    
    /* Animações */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    /* Loading Spinner Customizado */
    .stSpinner > div {
        border-color: var(--primary-color) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 10px 20px;
        background-color: var(--bg-light);
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color);
        color: white;
    }
    
    /* Download Buttons */
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--info-color) 0%, #138496 100%);
        color: white;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 20px;
        color: var(--text-secondary);
        font-size: 12px;
        border-top: 1px solid var(--border-color);
        margin-top: 40px;
    }
    </style>
    """, unsafe_allow_html=True)

apply_custom_css()

# ==================== FUNÇÕES OTIMIZADAS (CACHING) ====================

@st.cache_data(ttl=3600)
def get_specialty_list():
    """Retorna lista de especialidades (cached)."""
    return [
        "Clínica Médica",
        "Cardiologia",
        "Pneumologia",
        "Gastroenterologia",
        "Neurologia",
        "Pediatria",
        "Ginecologia/Obstetrícia",
        "Outros"
    ]

@st.cache_data
def get_app_info():
    """Retorna informações do app (cached)."""
    return {
        "version": "2.0.0",
        "name": "Assistente Médico Educacional",
        "description": "Sistema de apoio ao aprendizado clínico",
        "author": "Equipe Médica"
    }

def create_tooltip(text, tooltip_text):
    """Cria um texto com tooltip explicativo."""
    return f'{text} <span class="tooltip" data-tooltip="{tooltip_text}">ℹ️</span>'

def export_session_history():
    """Exporta o histórico completo da sessão em formato JSON."""
    history_data = {
        "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "export_date": datetime.now().isoformat(),
        "specialty": st.session_state.get('especialidade', 'N/A'),
        "context": st.session_state.get('dados_consulta', ''),
        "chat_history": st.session_state.get('chat_history', []),
        "diagnostics": st.session_state.get('diagnosticos', []),
        "suggestions": st.session_state.get('sugestoes', {}),
        "medical_record": st.session_state.get('prontuario_gerado', ''),
        "record_format": st.session_state.get('formato_prontuario', 'N/A')
    }
    
    # Converter datetime objects para strings
    if history_data['chat_history']:
        for item in history_data['chat_history']:
            if 'timestamp' in item and isinstance(item['timestamp'], datetime):
                item['timestamp'] = item['timestamp'].isoformat()
    
    return json.dumps(history_data, indent=2, ensure_ascii=False)

def save_consultation_to_history():
    """Salva consulta atual no histórico de consultas."""
    if 'consultation_history' not in st.session_state:
        st.session_state.consultation_history = []
    
    if st.session_state.diagnosticos and st.session_state.dados_consulta:
        consultation = {
            "id": len(st.session_state.consultation_history) + 1,
            "timestamp": datetime.now(),
            "specialty": st.session_state.especialidade,
            "context_preview": st.session_state.dados_consulta[:100] + "...",
            "num_diagnostics": len(st.session_state.diagnosticos),
            "top_diagnostic": st.session_state.diagnosticos[0]['nome'] if st.session_state.diagnosticos else "N/A"
        }
        
        # Evitar duplicatas
        if not any(c.get('timestamp') == consultation['timestamp'] for c in st.session_state.consultation_history):
            st.session_state.consultation_history.append(consultation)
            # Limitar histórico a 10 consultas
            if len(st.session_state.consultation_history) > 10:
                st.session_state.consultation_history = st.session_state.consultation_history[-10:]

def get_consultation_history_summary():
    """Retorna resumo do histórico de consultas."""
    if 'consultation_history' not in st.session_state or not st.session_state.consultation_history:
        return None
    
    history = st.session_state.consultation_history
    return {
        "total_consultations": len(history),
        "specialties": list(set(c['specialty'] for c in history)),
        "total_diagnostics": sum(c['num_diagnostics'] for c in history),
        "last_consultation": history[-1]['timestamp'] if history else None
    }

# Inicializar logger e logar sessão
logger = get_logger()
log_session_info()

# Validar API key do Gemini com validação robusta
logger.info("Validando API key do Gemini")
api_valid, api_error = validate_gemini_api_key()

if not api_valid:
    logger.error(f"Validação de API key falhou: {api_error}")
    st.error(f"⚠️ {api_error}")
    st.info("""
    **Como configurar:**
    1. Acesse [Google AI Studio](https://aistudio.google.com/apikey)
    2. Crie uma nova API Key
    3. Crie o diretório `.streamlit` no projeto
    4. Crie o arquivo `secrets.toml` dentro dele
    5. Adicione: `GEMINI_API_KEY = "sua_chave_aqui"`
    
    **Troubleshooting:**
    - Verifique se a API key está correta
    - Confirme se o Gemini API está habilitado no seu projeto Google
    - Certifique-se de que não excedeu os limites gratuitos
    """)
    st.stop()
else:
    logger.info("API key validada com sucesso")

# Inicializar session_state
if 'dados_consulta' not in st.session_state:
    st.session_state.dados_consulta = ""
if 'especialidade' not in st.session_state:
    st.session_state.especialidade = "Clínica Médica"
if 'diagnosticos' not in st.session_state:
    st.session_state.diagnosticos = None
if 'sugestoes' not in st.session_state:
    st.session_state.sugestoes = None
if 'analise_completa' not in st.session_state:
    st.session_state.analise_completa = None
if 'context_manager' not in st.session_state:
    st.session_state.context_manager = ContextManager()
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'last_api_call' not in st.session_state:
    st.session_state.last_api_call = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'prontuario_gerado' not in st.session_state:
    st.session_state.prontuario_gerado = None
if 'formato_prontuario' not in st.session_state:
    st.session_state.formato_prontuario = "Tradicional"

# Função para limpar sessão
def limpar_sessao():
    st.session_state.dados_consulta = ""
    st.session_state.especialidade = "Clínica Médica"
    st.session_state.diagnosticos = None
    st.session_state.sugestoes = None
    st.session_state.analise_completa = None
    st.session_state.context_manager.clear_context()
    st.session_state.chat_history = []
    st.session_state.last_api_call = None
    st.session_state.processing = False
    st.session_state.prontuario_gerado = None
    st.session_state.formato_prontuario = "Tradicional"
    st.rerun()

# Função de debouncing - verifica se pode fazer chamada à API
def can_make_api_call(min_interval_seconds=3):
    """
    Implementa debouncing para evitar chamadas excessivas à API.
    
    Args:
        min_interval_seconds: Intervalo mínimo entre chamadas em segundos
    
    Returns:
        True se pode fazer chamada, False caso contrário
    """
    if st.session_state.last_api_call is None:
        return True
    
    time_since_last_call = datetime.now() - st.session_state.last_api_call
    return time_since_last_call.total_seconds() >= min_interval_seconds

# Função para processar nova informação do chat
def process_chat_input(user_input):
    """
    Processa input do usuário e atualiza análise com validações robustas.
    
    Args:
        user_input: Texto enviado pelo usuário
    """
    logger.info("Processando input do usuário")
    
    # Validação básica de input
    if not user_input or not user_input.strip():
        logger.warning("Input vazio recebido")
        st.warning("⚠️ Por favor, digite alguma informação antes de enviar.")
        return
    
    # Verificar rate limiting
    can_proceed, rate_msg = check_rate_limit_status()
    if not can_proceed:
        logger.warning(f"Rate limit ativo: {rate_msg}")
        st.warning(rate_msg)
        return
    
    # Marcar como processando
    st.session_state.processing = True
    start_time = time.time()
    
    try:
        # Adicionar mensagem do usuário ao histórico
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now()
        })
        logger.info(f"Input adicionado ao histórico (len={len(user_input)})")
        
        # Adicionar ao contexto usando ContextManager
        st.session_state.context_manager.add_information(
            user_input,
            tipo="dados_paciente"
        )
        st.session_state.context_manager.set_especialidade(
            st.session_state.especialidade
        )
        
        # Obter contexto acumulado
        all_entries = st.session_state.context_manager.get_entries()
        st.session_state.dados_consulta = "\n\n".join([
            entry['conteudo'] for entry in all_entries
        ])
        
        # Validar se há contexto suficiente para análise
        context_valid, context_error = validate_context_for_analysis(
            st.session_state.dados_consulta
        )
        
        if not context_valid:
            logger.warning(f"Contexto insuficiente: {context_error}")
            st.warning(f"⚠️ {context_error}")
            st.session_state.processing = False
            return
        
        logger.info(f"Contexto validado (total={len(st.session_state.dados_consulta)} chars)")
        
        # Mostrar spinner e processar
        with st.spinner("🔄 Analisando informações com Gemini..."):
            try:
                # Obter handler do Gemini
                handler = get_gemini_handler()
                
                # Analisar caso
                analysis_start = time.time()
                resultado, erro = handler.analyze_case(
                    context=st.session_state.dados_consulta,
                    specialty=st.session_state.especialidade,
                    max_retries=3
                )
                analysis_duration = time.time() - analysis_start
                
                if erro:
                    friendly_error = get_friendly_error_message(Exception(erro))
                    logger.error(f"Análise falhou: {erro}")
                    st.error(friendly_error)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"Erro ao processar: {friendly_error}",
                        "timestamp": datetime.now()
                    })
                else:
                    logger.info(f"Análise concluída em {analysis_duration:.2f}s")
                    log_performance_metric("analyze_case", analysis_duration, True)
                    
                    # Armazenar resultados
                    st.session_state.analise_completa = resultado
                    st.session_state.diagnosticos = resultado.get('diagnosticos', [])
                    
                    logger.info(f"{len(st.session_state.diagnosticos)} diagnósticos gerados")
                    
                    # Gerar sugestões
                    with st.spinner("💡 Gerando sugestões clínicas..."):
                        try:
                            suggestions_start = time.time()
                            sugestoes = handler.generate_suggestions(
                                context=st.session_state.dados_consulta,
                                specialty=st.session_state.especialidade,
                                diagnosticos=st.session_state.diagnosticos,
                                max_retries=2
                            )
                            suggestions_duration = time.time() - suggestions_start
                            
                            st.session_state.sugestoes = sugestoes
                            
                            if sugestoes:
                                logger.info(f"Sugestões geradas em {suggestions_duration:.2f}s")
                                log_performance_metric("generate_suggestions", suggestions_duration, True)
                        except Exception as e:
                            logger.error(f"Erro ao gerar sugestões: {str(e)}")
                            log_exception(e, "generate_suggestions")
                            # Não bloquear se sugestões falharem
                    
                    # Adicionar resposta ao histórico
                    num_diagnosticos = len(st.session_state.diagnosticos)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"✅ Análise concluída! {num_diagnosticos} hipóteses diagnósticas geradas.",
                        "timestamp": datetime.now()
                    })
                    
                    # Salvar consulta no histórico
                    save_consultation_to_history()
                    logger.info("Consulta salva no histórico")
                    
                    # Atualizar timestamp da última chamada
                    st.session_state.last_api_call = datetime.now()
                    
            except Exception as e:
                friendly_error = get_friendly_error_message(e)
                logger.error(f"Erro na chamada de API: {str(e)}")
                log_exception(e, "process_chat_input - API call")
                st.error(friendly_error)
                
    except Exception as e:
        friendly_error = get_friendly_error_message(e)
        logger.error(f"Erro geral no processamento: {str(e)}")
        log_exception(e, "process_chat_input - general")
        st.error(f"❌ {friendly_error}")
    finally:
        st.session_state.processing = False
        total_duration = time.time() - start_time
        logger.info(f"Processamento total: {total_duration:.2f}s")
        log_performance_metric("process_chat_input", total_duration, True)

# Função para obter cor baseada na probabilidade
def get_probability_color(probability):
    """
    Retorna cor baseada na probabilidade (gradiente).
    Vermelho (alta) -> Amarelo (média) -> Verde (baixa)
    """
    if probability >= 70:
        # Alta probabilidade - tons de vermelho
        return "#dc3545"  # Vermelho
    elif probability >= 40:
        # Média probabilidade - tons de laranja/amarelo
        return "#ffc107"  # Amarelo/Laranja
    else:
        # Baixa probabilidade - tons de verde
        return "#28a745"  # Verde

# Função para exibir ranking de diagnósticos
def display_diagnostic_ranking(diagnoses_data):
    """
    Exibe ranking de diagnósticos com barras de progresso coloridas.
    
    Args:
        diagnoses_data: Lista de diagnósticos com probabilidades
    """
    if not diagnoses_data or len(diagnoses_data) == 0:
        st.info("📋 Nenhum diagnóstico disponível ainda.")
        return
    
    # Ordenar por probabilidade (maior para menor)
    sorted_diagnoses = sorted(
        diagnoses_data,
        key=lambda x: x.get('probabilidade', 0),
        reverse=True
    )
    
    # Limitar aos top 5
    top_diagnoses = sorted_diagnoses[:5]
    
    st.markdown("### 🎯 Ranking de Probabilidades")
    st.markdown("---")
    
    for idx, diag in enumerate(top_diagnoses, 1):
        nome = diag.get('nome', 'Diagnóstico Desconhecido')
        probabilidade = diag.get('probabilidade', 0)
        
        # Obter cor baseada na probabilidade
        cor = get_probability_color(probabilidade)
        
        # Container para cada diagnóstico
        st.markdown(f"**{idx}. {nome}**")
        
        # Barra de progresso com cor customizada
        st.markdown(
            f"""
            <div style="background-color: #e0e0e0; border-radius: 10px; overflow: hidden; margin-bottom: 5px;">
                <div style="background-color: {cor}; width: {probabilidade}%; padding: 8px 10px; 
                            text-align: center; color: white; font-weight: bold; border-radius: 10px 0 0 10px;">
                    {probabilidade}%
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Expander com detalhes
        with st.expander("📖 Ver detalhes"):
            if 'justificativa' in diag:
                st.markdown("**Justificativa:**")
                st.write(diag['justificativa'])
            
            if 'evidencias_favor' in diag and diag['evidencias_favor']:
                st.markdown("**✅ Evidências a Favor:**")
                for ev in diag['evidencias_favor']:
                    st.write(f"• {ev}")
            
            if 'evidencias_contra' in diag and diag['evidencias_contra']:
                st.markdown("**❌ Evidências Contra:**")
                for ev in diag['evidencias_contra']:
                    st.write(f"• {ev}")
            
            if 'dados_principais' in diag and diag['dados_principais']:
                st.markdown("**📌 Dados Principais:**")
                for dado in diag['dados_principais']:
                    st.write(f"• {dado}")
        
        st.markdown("")  # Espaço entre diagnósticos

# Função para exibir sugestões
def display_suggestions(suggestions_data):
    """
    Exibe sugestões clínicas com expanders e ícones.
    
    Args:
        suggestions_data: Dicionário com sugestões (follow_up_questions, suggested_exams, management_suggestions)
    """
    if not suggestions_data:
        st.info("💡 Nenhuma sugestão disponível ainda.")
        return
    
    # Perguntas de Seguimento
    if 'follow_up_questions' in suggestions_data and suggestions_data['follow_up_questions']:
        with st.expander("❓ **Perguntas de Seguimento**", expanded=True):
            st.markdown("*Perguntas importantes para complementar a investigação:*")
            st.markdown("")
            for idx, pergunta in enumerate(suggestions_data['follow_up_questions'], 1):
                st.markdown(f"**{idx}.** {pergunta}")
                if idx < len(suggestions_data['follow_up_questions']):
                    st.markdown("")
    
    # Exames Complementares
    if 'suggested_exams' in suggestions_data and suggestions_data['suggested_exams']:
        with st.expander("🔬 **Exames Complementares**", expanded=True):
            st.markdown("*Exames prioritários para este caso:*")
            st.markdown("")
            for idx, exame in enumerate(suggestions_data['suggested_exams'], 1):
                st.markdown(f"**{idx}.** {exame}")
                if idx < len(suggestions_data['suggested_exams']):
                    st.markdown("")
    
    # Sugestões de Conduta/Manejo
    if 'management_suggestions' in suggestions_data and suggestions_data['management_suggestions']:
        with st.expander("💊 **Sugestões de Conduta**", expanded=True):
            st.markdown("*Recomendações de manejo clínico:*")
            st.markdown("")
            for idx, conduta in enumerate(suggestions_data['management_suggestions'], 1):
                st.markdown(f"**{idx}.** {conduta}")
                if idx < len(suggestions_data['management_suggestions']):
                    st.markdown("")

# Título principal
st.title("🩺 Assistente de Consulta Médica - Estudante")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Seletor de especialidade (usando função cached)
    especialidades = get_specialty_list()
    
    st.markdown(create_tooltip("🏥 **Especialidade Médica**", "Escolha a especialidade mais adequada para o caso clínico"), unsafe_allow_html=True)
    st.session_state.especialidade = st.selectbox(
        "Selecione a especialidade:",
        options=especialidades,
        index=especialidades.index(st.session_state.especialidade),
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Botão para limpar sessão
    if st.button("🔄 Começar Nova Consulta", use_container_width=True, type="primary"):
        limpar_sessao()
    
    st.markdown("---")
    
    # Status do sistema
    st.markdown("#### 📊 Status")
    
    # Informações do contexto
    if st.session_state.context_manager.has_entries():
        summary = st.session_state.context_manager.get_summary()
        st.metric("Informações Adicionadas", summary['total_entradas'])
    else:
        st.metric("Informações Adicionadas", 0)
    
    # Status de processamento
    if st.session_state.processing:
        st.warning("🔄 Processando...")
    elif st.session_state.diagnosticos:
        st.success(f"✅ {len(st.session_state.diagnosticos)} diagnósticos")
    else:
        st.info("⏳ Aguardando dados")
    
    # Debouncing info
    if st.session_state.last_api_call:
        time_since = (datetime.now() - st.session_state.last_api_call).total_seconds()
        if time_since < 3:
            st.caption(f"⏱️ Próxima análise em {3 - int(time_since)}s")
    
    st.markdown("---")
    st.info("👨‍⚕️ Ferramenta educacional para auxiliar estudantes de medicina")
    
    # Dicas de uso
    with st.expander("💡 Dicas de Uso"):
        st.markdown("""
        **Como usar o sistema:**
        
        1. **Adicione informações progressivamente** - Digite dados do paciente e clique em "Enviar e Analisar"
        
        2. **Aguarde o intervalo de 3 segundos** entre análises (debouncing)
        
        3. **Observe as atualizações** nas colunas de diagnósticos e sugestões
        
        4. **Use "Começar Nova Consulta"** para resetar tudo
        
        **Exemplos de informações:**
        - Dados demográficos
        - Queixa principal
        - História da doença
        - Exame físico
        - Resultados de exames
        """)
    
    st.markdown("---")
    
    # Exportação do Histórico Completo
    st.markdown("#### 📥 Exportar Histórico")
    
    if st.session_state.chat_history or st.session_state.diagnosticos:
        history_json = export_session_history()
        st.download_button(
            label="💾 Baixar Sessão Completa",
            data=history_json,
            file_name=f"sessao_medica_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
            help="Baixa todo o histórico da sessão atual em formato JSON"
        )
    else:
        st.info("Nenhum dado para exportar ainda")
    
    st.markdown("---")
    
    # Histórico de Consultas Anteriores
    history_summary = get_consultation_history_summary()
    
    if history_summary:
        st.markdown("#### 📚 Histórico de Consultas")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", history_summary['total_consultations'])
        with col2:
            st.metric("Diagnósticos", history_summary['total_diagnostics'])
        
        with st.expander("📋 Ver Consultas Anteriores", expanded=False):
            if 'consultation_history' in st.session_state and st.session_state.consultation_history:
                for consultation in reversed(st.session_state.consultation_history[-5:]):  # Últimas 5
                    st.markdown(f"""
                    **Consulta #{consultation['id']}** - {consultation['specialty']}  
                    🕒 {consultation['timestamp'].strftime('%d/%m/%Y %H:%M')}  
                    🎯 {consultation['top_diagnostic']}  
                    📊 {consultation['num_diagnostics']} diagnósticos
                    """)
                    st.markdown("---")
    
    st.markdown("---")

# Conteúdo principal
def main():
    # Layout com 3 colunas
    col_left, col_center, col_right = st.columns([0.4, 0.3, 0.3])
    
    # Coluna esquerda (40%) - Input de dados da consulta
    with col_left:
        st.markdown(create_tooltip("## 📝 Informações do Caso", "Adicione dados do paciente progressivamente. O sistema analisará e atualizará os diagnósticos automaticamente."), unsafe_allow_html=True)
        
        # Mostrar histórico do chat/contexto
        chat_container = st.container()
        with chat_container:
            if st.session_state.chat_history:
                st.markdown("#### 💬 Histórico de Informações")
                # Exibir mensagens em ordem cronológica
                for msg in st.session_state.chat_history[-10:]:  # Últimas 10 mensagens
                    if msg['role'] == 'user':
                        st.markdown(f"**👤 Você ({msg['timestamp'].strftime('%H:%M')})**")
                        st.info(msg['content'])
                    else:
                        st.markdown(f"**🤖 Sistema ({msg['timestamp'].strftime('%H:%M')})**")
                        st.success(msg['content'])
                st.markdown("---")
        
        # Formulário para novo input
        with st.form(key="input_form", clear_on_submit=True):
            st.markdown("#### ➕ Adicionar Informação")
            
            user_input = st.text_area(
                "Digite novas informações sobre o caso:",
                height=150,
                placeholder="""Exemplos de informações a adicionar:

• Queixa principal do paciente
• História da doença atual
• Antecedentes pessoais ou familiares
• Dados do exame físico
• Sinais vitais
• Resultados de exames complementares
• Evolução do quadro

Digite Enter ou clique em Enviar para processar.""",
                help="Adicione informações progressivamente. O sistema irá analisá-las e atualizar os diagnósticos.",
                disabled=st.session_state.processing
            )
            
            # Botões do formulário
            col_btn1, col_btn2 = st.columns([0.7, 0.3])
            
            with col_btn1:
                submit_button = st.form_submit_button(
                    "📤 Enviar e Analisar",
                    use_container_width=True,
                    type="primary",
                    disabled=st.session_state.processing
                )
            
            with col_btn2:
                # Indicador de debouncing
                if st.session_state.last_api_call:
                    time_since = (datetime.now() - st.session_state.last_api_call).total_seconds()
                    if time_since < 3:
                        remaining = 3 - int(time_since)
                        st.caption(f"⏱️ {remaining}s")
                    else:
                        st.caption("✅ Pronto")
        
        # Processar quando formulário é submetido
        if submit_button and user_input:
            process_chat_input(user_input)
            st.rerun()
        
        # Mostrar resumo do contexto acumulado
        if st.session_state.context_manager.has_entries():
            with st.expander("📊 Resumo do Contexto Acumulado"):
                summary = st.session_state.context_manager.get_summary()
                st.metric("Total de Entradas", summary['total_entradas'])
                st.write(f"**Especialidade:** {summary['especialidade']}")
                
                # Botão para visualizar contexto completo
                if st.button("📄 Ver Contexto Completo"):
                    st.text_area(
                        "Contexto Formatado",
                        value=st.session_state.context_manager.get_full_context(),
                        height=200
                    )
    
    # Coluna central (30%) - Ranking de probabilidades diagnósticas
    with col_center:
        st.markdown(create_tooltip("## 📊 Hipóteses Diagnósticas", "Diagnósticos diferenciais ranqueados por probabilidade baseados nos dados fornecidos"), unsafe_allow_html=True)
        
        # Exibir diagnósticos ou placeholder
        if st.session_state.diagnosticos:
            display_diagnostic_ranking(st.session_state.diagnosticos)
            
            # Exibir informações adicionais se disponíveis
            if st.session_state.analise_completa:
                st.markdown("---")
                
                # Nível de confiança
                if 'nivel_confianca' in st.session_state.analise_completa:
                    nivel = st.session_state.analise_completa['nivel_confianca']
                    if nivel == 'alto':
                        st.success(f"🎯 Confiança: **{nivel.upper()}**")
                    elif nivel == 'medio':
                        st.warning(f"⚠️ Confiança: **{nivel.upper()}**")
                    else:
                        st.info(f"ℹ️ Confiança: **{nivel.upper()}**")
                
                # Observações
                if 'observacoes' in st.session_state.analise_completa:
                    with st.expander("📝 Observações Importantes"):
                        st.write(st.session_state.analise_completa['observacoes'])
                
                # Dados insuficientes
                if 'dados_insuficientes' in st.session_state.analise_completa:
                    dados_faltantes = st.session_state.analise_completa['dados_insuficientes']
                    if dados_faltantes:
                        with st.expander("⚠️ Dados Insuficientes"):
                            for dado in dados_faltantes:
                                st.write(f"• {dado}")
        else:
            # Placeholder quando não há diagnósticos
            st.markdown("""
            <div style='background-color: #f0f2f6; padding: 15px; border-radius: 5px; min-height: 400px;'>
                <p><strong>🎯 Ranking de Probabilidades</strong></p>
                <p style='color: #666;'>Os diagnósticos mais prováveis aparecerão aqui após a análise do caso.</p>
                <hr>
                <p style='font-size: 0.9em;'>
                    • Diagnóstico 1<br>
                    • Diagnóstico 2<br>
                    • Diagnóstico 3<br>
                    • Diagnóstico 4<br>
                    • Diagnóstico 5
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Coluna direita (30%) - Sugestões
    with col_right:
        st.markdown(create_tooltip("## 💡 Sugestões Clínicas", "Perguntas, exames e condutas recomendadas para investigação do caso"), unsafe_allow_html=True)
        
        # Exibir sugestões usando a função dedicada
        if st.session_state.sugestoes:
            display_suggestions(st.session_state.sugestoes)
        else:
            # Placeholder quando não há sugestões
            st.markdown("""
            <div style='background-color: #e8f4f8; padding: 15px; border-radius: 5px; min-height: 400px;'>
                <p><strong>💡 Aguardando Análise</strong></p>
                <p style='color: #666; font-size: 0.9em;'>
                    Após analisar o caso, sugestões clínicas aparecerão aqui organizadas em:
                </p>
                <hr>
                <p style='color: #555; font-size: 0.85em;'>
                    ❓ <strong>Perguntas de Seguimento</strong><br>
                    <span style='color: #666;'>Perguntas complementares para investigação</span>
                </p>
                <hr>
                <p style='color: #555; font-size: 0.85em;'>
                    🔬 <strong>Exames Complementares</strong><br>
                    <span style='color: #666;'>Exames prioritários recomendados</span>
                </p>
                <hr>
                <p style='color: #555; font-size: 0.85em;'>
                    💊 <strong>Sugestões de Conduta</strong><br>
                    <span style='color: #666;'>Recomendações de manejo clínico</span>
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Rodapé - Geração de prontuário
    st.markdown("---")
    
    footer_col1, footer_col2, footer_col3 = st.columns([0.3, 0.3, 0.4])
    
    with footer_col1:
        formato_prontuario = st.selectbox(
            "📋 Formato do Prontuário",
            options=["Tradicional", "SOAP"],
            help="Escolha o formato de registro médico"
        )
    
    with footer_col2:
        if st.button("📄 Gerar Prontuário", use_container_width=True, type="secondary"):
            if st.session_state.dados_consulta.strip():
                with st.spinner(f"🔄 Gerando prontuário no formato {formato_prontuario}..."):
                    generator = get_medical_record_generator()
                    
                    # Gerar prontuário baseado no formato selecionado
                    if formato_prontuario == "SOAP":
                        prontuario, erro = generator.generate_soap_record(
                            context=st.session_state.dados_consulta,
                            diagnosticos=st.session_state.diagnosticos
                        )
                    else:  # Tradicional
                        prontuario, erro = generator.generate_traditional_record(
                            context=st.session_state.dados_consulta,
                            diagnosticos=st.session_state.diagnosticos
                        )
                    
                    if prontuario:
                        st.session_state.prontuario_gerado = prontuario
                        st.session_state.formato_prontuario = formato_prontuario
                        st.success("✅ Prontuário gerado com sucesso!")
                    else:
                        st.error(f"❌ Erro ao gerar prontuário: {erro}")
            else:
                st.error("⚠️ Insira os dados da consulta primeiro.")
    
    with footer_col3:
        st.markdown("")  # Espaço vazio
    
    # Exibir prontuário gerado se disponível
    if st.session_state.prontuario_gerado:
        st.markdown("---")
        
        with st.expander(f"📄 Prontuário Gerado - Formato {st.session_state.formato_prontuario}", expanded=True):
            # Exibir prontuário em Markdown
            st.markdown(st.session_state.prontuario_gerado)
            
            st.markdown("---")
            
            # Opções de download
            col_download1, col_download2, col_download3 = st.columns([0.3, 0.3, 0.4])
            
            with col_download1:
                # Download como TXT
                st.download_button(
                    label="💾 Download TXT",
                    data=st.session_state.prontuario_gerado,
                    file_name=f"prontuario_{st.session_state.formato_prontuario.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col_download2:
                # Download como Markdown
                st.download_button(
                    label="📝 Download MD",
                    data=st.session_state.prontuario_gerado,
                    file_name=f"prontuario_{st.session_state.formato_prontuario.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            with col_download3:
                # Botão para limpar prontuário
                if st.button("🗑️ Limpar Prontuário", use_container_width=True):
                    st.session_state.prontuario_gerado = None
                    st.rerun()
    
    # Rodapé
    st.markdown("---")
    app_info = get_app_info()
    st.markdown(f"""
    <div class="footer">
        <p><strong>{app_info['name']}</strong> v{app_info['version']}</p>
        <p>{app_info['description']}</p>
        <p>⚠️ <em>Esta é uma ferramenta educacional. Não substitui avaliação médica profissional.</em></p>
        <p style="margin-top: 10px; font-size: 10px;">
            © 2025 {app_info['author']} | Desenvolvido com ❤️ para educação médica
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

