"""
Context Manager para gerenciar o histórico e contexto das consultas médicas.
Integrado com Streamlit session_state para persistência durante a sessão.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional
import json


class ContextManager:
    """
    Gerencia o contexto e histórico de consultas médicas.
    Armazena informações no session_state do Streamlit para persistência.
    """
    
    def __init__(self, session_key: str = "medical_context"):
        """
        Inicializa o gerenciador de contexto.
        
        Args:
            session_key: Chave para armazenar no st.session_state
        """
        self.session_key = session_key
        
        # Inicializar no session_state se não existir
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = self._create_empty_context()
    
    def _create_empty_context(self) -> Dict:
        """
        Cria um contexto vazio com estrutura padrão.
        
        Returns:
            Dicionário com estrutura inicial do contexto
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "especialidade": "Clínica Médica",
            "entries": []
        }
    
    def add_information(self, texto: str, tipo: str = "info") -> None:
        """
        Adiciona uma nova entrada de informação ao contexto.
        
        Args:
            texto: Texto da informação a ser adicionada
            tipo: Tipo da entrada (info, diagnostico, sugestao, etc.)
        """
        if not texto or not texto.strip():
            return
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "tipo": tipo,
            "conteudo": texto.strip()
        }
        
        st.session_state[self.session_key]["entries"].append(entry)
    
    def set_especialidade(self, especialidade: str) -> None:
        """
        Define a especialidade médica do contexto atual.
        
        Args:
            especialidade: Nome da especialidade médica
        """
        st.session_state[self.session_key]["especialidade"] = especialidade
    
    def get_especialidade(self) -> str:
        """
        Retorna a especialidade médica atual.
        
        Returns:
            Nome da especialidade
        """
        return st.session_state[self.session_key].get("especialidade", "Clínica Médica")
    
    def get_full_context(self, format_type: str = "text") -> str:
        """
        Retorna todo o histórico formatado.
        
        Args:
            format_type: Tipo de formatação ('text' ou 'json')
        
        Returns:
            Contexto formatado como string
        """
        context = st.session_state[self.session_key]
        
        if format_type == "json":
            return json.dumps(context, indent=2, ensure_ascii=False)
        
        # Formatação em texto
        formatted_text = []
        formatted_text.append("=" * 60)
        formatted_text.append("CONTEXTO DA CONSULTA MÉDICA")
        formatted_text.append("=" * 60)
        formatted_text.append(f"\nEspecialidade: {context['especialidade']}")
        formatted_text.append(f"Iniciado em: {self._format_timestamp(context['timestamp'])}")
        formatted_text.append(f"Total de entradas: {len(context['entries'])}")
        formatted_text.append("\n" + "-" * 60)
        
        if context['entries']:
            formatted_text.append("\nHISTÓRICO DE ENTRADAS:\n")
            for idx, entry in enumerate(context['entries'], 1):
                formatted_text.append(f"\n[{idx}] {entry['tipo'].upper()}")
                formatted_text.append(f"Timestamp: {self._format_timestamp(entry['timestamp'])}")
                formatted_text.append(f"Conteúdo: {entry['conteudo']}")
                formatted_text.append("-" * 60)
        else:
            formatted_text.append("\nNenhuma entrada registrada ainda.")
        
        return "\n".join(formatted_text)
    
    def get_context_dict(self) -> Dict:
        """
        Retorna o contexto completo como dicionário.
        
        Returns:
            Dicionário com todo o contexto
        """
        return st.session_state[self.session_key].copy()
    
    def get_entries(self) -> List[Dict]:
        """
        Retorna apenas a lista de entradas.
        
        Returns:
            Lista de entradas do histórico
        """
        return st.session_state[self.session_key]["entries"].copy()
    
    def get_entries_by_type(self, tipo: str) -> List[Dict]:
        """
        Retorna entradas filtradas por tipo.
        
        Args:
            tipo: Tipo de entrada a filtrar
        
        Returns:
            Lista de entradas do tipo especificado
        """
        return [
            entry for entry in st.session_state[self.session_key]["entries"]
            if entry["tipo"] == tipo
        ]
    
    def clear_context(self) -> None:
        """
        Limpa todo o histórico e reinicia o contexto.
        """
        st.session_state[self.session_key] = self._create_empty_context()
    
    def get_summary(self) -> Dict:
        """
        Retorna um resumo estatístico do contexto.
        
        Returns:
            Dicionário com estatísticas do contexto
        """
        context = st.session_state[self.session_key]
        entries = context["entries"]
        
        # Contar por tipo
        tipos_count = {}
        for entry in entries:
            tipo = entry["tipo"]
            tipos_count[tipo] = tipos_count.get(tipo, 0) + 1
        
        return {
            "especialidade": context["especialidade"],
            "timestamp_inicio": context["timestamp"],
            "total_entradas": len(entries),
            "tipos_distribuicao": tipos_count,
            "primeira_entrada": entries[0]["timestamp"] if entries else None,
            "ultima_entrada": entries[-1]["timestamp"] if entries else None
        }
    
    def export_to_json(self) -> str:
        """
        Exporta o contexto completo para JSON.
        
        Returns:
            String JSON com todo o contexto
        """
        return json.dumps(
            st.session_state[self.session_key],
            indent=2,
            ensure_ascii=False
        )
    
    def import_from_json(self, json_string: str) -> bool:
        """
        Importa contexto de uma string JSON.
        
        Args:
            json_string: String JSON com contexto
        
        Returns:
            True se importação foi bem-sucedida, False caso contrário
        """
        try:
            context = json.loads(json_string)
            
            # Validar estrutura básica
            if not all(key in context for key in ["timestamp", "especialidade", "entries"]):
                return False
            
            st.session_state[self.session_key] = context
            return True
        except (json.JSONDecodeError, Exception):
            return False
    
    def _format_timestamp(self, timestamp_str: str) -> str:
        """
        Formata timestamp para exibição legível.
        
        Args:
            timestamp_str: String ISO do timestamp
        
        Returns:
            String formatada para exibição
        """
        try:
            dt = datetime.fromisoformat(timestamp_str)
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        except (ValueError, Exception):
            return timestamp_str
    
    def has_entries(self) -> bool:
        """
        Verifica se há entradas no contexto.
        
        Returns:
            True se há entradas, False caso contrário
        """
        return len(st.session_state[self.session_key]["entries"]) > 0

