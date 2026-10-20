"""Ponto de extensão: futura IA recebe dados verificados, nunca publica."""
from typing import Protocol


class EditorialWriter(Protocol):
    def draft(self, articles: list[dict]) -> str:
        """Produz apenas um rascunho para revisão humana, preservando referências."""
        ...
