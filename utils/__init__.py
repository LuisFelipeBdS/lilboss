"""
Módulo de utilitários para o Assistente de Consulta Médica.
"""

from .context_manager import ContextManager
from .gemini_handler import GeminiHandler, analyze_case, get_gemini_handler
from .medical_record_generator import (
    MedicalRecordGenerator,
    generate_traditional_record,
    generate_soap_record,
    get_medical_record_generator
)
from .validators import (
    validate_gemini_api_key,
    validate_context_for_analysis,
    validate_diagnosticos,
    check_minimum_data_for_prontuario,
    sanitize_input,
    validate_specialty,
    get_validation_summary,
    get_friendly_error_message,
    check_rate_limit_status
)
from .logger import (
    get_logger,
    log_session_info,
    log_exception,
    log_performance_metric,
    log_function_call,
    LogBlock,
    AppLogger
)

__all__ = [
    'ContextManager',
    'GeminiHandler',
    'analyze_case',
    'get_gemini_handler',
    'MedicalRecordGenerator',
    'generate_traditional_record',
    'generate_soap_record',
    'get_medical_record_generator',
    'validate_gemini_api_key',
    'validate_context_for_analysis',
    'validate_diagnosticos',
    'check_minimum_data_for_prontuario',
    'sanitize_input',
    'validate_specialty',
    'get_validation_summary',
    'get_friendly_error_message',
    'check_rate_limit_status',
    'get_logger',
    'log_session_info',
    'log_exception',
    'log_performance_metric',
    'log_function_call',
    'LogBlock',
    'AppLogger'
]

