"""
Logger - Sistema de logging para debugging e monitoramento.

Este módulo fornece logging estruturado para o sistema.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import streamlit as st


class AppLogger:
    """
    Logger customizado para a aplicação.
    """
    
    def __init__(self, name: str = "MedicalAssistant", log_file: Optional[str] = None):
        """
        Inicializa o logger.
        
        Args:
            name: Nome do logger
            log_file: Caminho do arquivo de log (opcional)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar duplicação de handlers
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            
            # File handler (se especificado)
            if log_file:
                try:
                    log_path = Path(log_file)
                    log_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    file_handler = logging.FileHandler(log_file, encoding='utf-8')
                    file_handler.setLevel(logging.DEBUG)
                    file_formatter = logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                    )
                    file_handler.setFormatter(file_formatter)
                    self.logger.addHandler(file_handler)
                except Exception as e:
                    print(f"Não foi possível criar arquivo de log: {e}")
    
    def debug(self, message: str, **kwargs):
        """Log de debug."""
        self.logger.debug(self._format_message(message, kwargs))
    
    def info(self, message: str, **kwargs):
        """Log de informação."""
        self.logger.info(self._format_message(message, kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log de aviso."""
        self.logger.warning(self._format_message(message, kwargs))
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log de erro."""
        msg = self._format_message(message, kwargs)
        if error:
            msg += f" | Erro: {str(error)}"
        self.logger.error(msg, exc_info=error is not None)
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log crítico."""
        msg = self._format_message(message, kwargs)
        if error:
            msg += f" | Erro: {str(error)}"
        self.logger.critical(msg, exc_info=error is not None)
    
    def _format_message(self, message: str, context: dict) -> str:
        """
        Formata mensagem com contexto adicional.
        
        Args:
            message: Mensagem base
            context: Contexto adicional
        
        Returns:
            Mensagem formatada
        """
        if not context:
            return message
        
        context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
        return f"{message} | {context_str}"
    
    def log_api_call(self, endpoint: str, success: bool, duration: float, **kwargs):
        """
        Log específico para chamadas de API.
        
        Args:
            endpoint: Nome do endpoint/função
            success: Se foi bem-sucedida
            duration: Duração em segundos
            **kwargs: Contexto adicional
        """
        status = "SUCCESS" if success else "FAILED"
        self.info(
            f"API Call: {endpoint}",
            status=status,
            duration_s=f"{duration:.2f}",
            **kwargs
        )
    
    def log_user_action(self, action: str, **kwargs):
        """
        Log de ações do usuário.
        
        Args:
            action: Descrição da ação
            **kwargs: Contexto adicional
        """
        self.info(f"User Action: {action}", **kwargs)
    
    def log_validation_error(self, validation: str, reason: str, **kwargs):
        """
        Log de erro de validação.
        
        Args:
            validation: Tipo de validação
            reason: Razão da falha
            **kwargs: Contexto adicional
        """
        self.warning(
            f"Validation Failed: {validation}",
            reason=reason,
            **kwargs
        )


# Instância global do logger
_global_logger: Optional[AppLogger] = None


def get_logger(name: str = "MedicalAssistant") -> AppLogger:
    """
    Retorna instância do logger (singleton).
    
    Args:
        name: Nome do logger
    
    Returns:
        Instância do AppLogger
    """
    global _global_logger
    
    if _global_logger is None:
        # Tentar criar arquivo de log na pasta logs/
        try:
            log_file = "logs/app.log"
        except:
            log_file = None
        
        _global_logger = AppLogger(name, log_file)
    
    return _global_logger


def log_session_info():
    """
    Loga informações da sessão atual.
    """
    logger = get_logger()
    
    if 'session_logged' not in st.session_state:
        logger.info(
            "Nova Sessão Iniciada",
            timestamp=datetime.now().isoformat()
        )
        st.session_state.session_logged = True


def log_exception(exception: Exception, context: str = ""):
    """
    Loga exceção com contexto.
    
    Args:
        exception: Exceção capturada
        context: Contexto adicional
    """
    logger = get_logger()
    logger.error(
        f"Exception caught: {context}",
        error=exception,
        exception_type=type(exception).__name__
    )


def log_performance_metric(operation: str, duration: float, success: bool = True):
    """
    Loga métrica de performance.
    
    Args:
        operation: Nome da operação
        duration: Duração em segundos
        success: Se foi bem-sucedida
    """
    logger = get_logger()
    logger.info(
        f"Performance: {operation}",
        duration_s=f"{duration:.2f}",
        success=success
    )


# Decorador para logging automático de funções
def log_function_call(func):
    """
    Decorador para logar chamadas de função.
    
    Args:
        func: Função a decorar
    
    Returns:
        Função decorada
    """
    def wrapper(*args, **kwargs):
        logger = get_logger()
        func_name = func.__name__
        
        logger.debug(f"Calling function: {func_name}")
        
        try:
            import time
            start_time = time.time()
            
            result = func(*args, **kwargs)
            
            duration = time.time() - start_time
            logger.debug(
                f"Function completed: {func_name}",
                duration_s=f"{duration:.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Function failed: {func_name}",
                error=e
            )
            raise
    
    return wrapper


# Context manager para logging de blocos
class LogBlock:
    """
    Context manager para logar blocos de código.
    """
    
    def __init__(self, block_name: str, logger: Optional[AppLogger] = None):
        """
        Inicializa bloco de log.
        
        Args:
            block_name: Nome do bloco
            logger: Logger a usar (opcional)
        """
        self.block_name = block_name
        self.logger = logger or get_logger()
        self.start_time = None
    
    def __enter__(self):
        """Início do bloco."""
        import time
        self.start_time = time.time()
        self.logger.debug(f"Starting block: {self.block_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Fim do bloco."""
        import time
        duration = time.time() - self.start_time
        
        if exc_type is not None:
            self.logger.error(
                f"Block failed: {self.block_name}",
                error=exc_val,
                duration_s=f"{duration:.2f}"
            )
        else:
            self.logger.debug(
                f"Block completed: {self.block_name}",
                duration_s=f"{duration:.2f}"
            )
        
        return False  # Não suprimir exceções


# Função para configurar nível de log via ambiente
def configure_log_level(level: str = "INFO"):
    """
    Configura nível de log.
    
    Args:
        level: Nível desejado (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger = get_logger()
    
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    log_level = level_map.get(level.upper(), logging.INFO)
    logger.logger.setLevel(log_level)

