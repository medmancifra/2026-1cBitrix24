"""
Kanban Bundle — Mini-App for Bitrix24 Task/CRM Kanban Board Management

Features:
- Manage Kanban stages (columns)
- Move tasks/items between stages
- Get board state with items per stage
- Kanban health status reporting (for vitrine view)
"""

from .board import KanbanBoard
from .models import KanbanStage, KanbanCard

__all__ = ["KanbanBoard", "KanbanStage", "KanbanCard"]
