"""
Data models for the Kanban bundle.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class CardStatus(Enum):
    """Maps to Bitrix24 task status codes."""
    PENDING = 1         # Не начата / Pending
    IN_PROGRESS = 3     # Выполняется / In Progress
    SUPPOSEDLY_DONE = 4 # Ждёт контроля / Waiting for control
    DONE = 5            # Завершена / Done
    DEFERRED = 6        # Отложена / Deferred


@dataclass
class KanbanStage:
    """Represents a single column on the Kanban board."""
    id: int
    title: str
    sort: int = 0
    color: str = ""
    entity_type: int = 1  # 1=My tasks, 2=Group
    task_count: int = 0

    @classmethod
    def from_api(cls, data: dict) -> "KanbanStage":
        return cls(
            id=int(data.get("ID", 0) or data.get("id", 0)),
            title=data.get("TITLE", data.get("title", "")),
            sort=int(data.get("SORT", data.get("sort", 0))),
            color=data.get("COLOR", data.get("color", "")),
            entity_type=int(data.get("ENTITY_TYPE", 1)),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "sort": self.sort,
            "color": self.color,
            "entity_type": self.entity_type,
            "task_count": self.task_count,
        }


@dataclass
class KanbanCard:
    """Represents a task card on the Kanban board."""
    id: int
    title: str
    stage_id: int
    responsible_id: Optional[int] = None
    deadline: Optional[str] = None
    status: int = 1
    group_id: Optional[int] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    created_date: Optional[str] = None

    @classmethod
    def from_task_api(cls, data: dict) -> "KanbanCard":
        """Creates a KanbanCard from task.item.list response."""
        return cls(
            id=int(data.get("ID", 0)),
            title=data.get("TITLE", ""),
            stage_id=int(data.get("STAGE_ID", 0)),
            responsible_id=data.get("RESPONSIBLE_ID"),
            deadline=data.get("DEADLINE"),
            status=int(data.get("STATUS", 1)),
            group_id=data.get("GROUP_ID"),
            description=data.get("DESCRIPTION", ""),
            tags=data.get("TAG", []) if isinstance(data.get("TAG"), list) else [],
            created_date=data.get("CREATED_DATE"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "stage_id": self.stage_id,
            "responsible_id": self.responsible_id,
            "deadline": self.deadline,
            "status": self.status,
            "group_id": self.group_id,
            "description": self.description,
            "tags": self.tags,
            "created_date": self.created_date,
        }


@dataclass
class BoardState:
    """Complete Kanban board state — all stages with their cards."""
    stages: List[KanbanStage] = field(default_factory=list)
    cards: List[KanbanCard] = field(default_factory=list)
    total_cards: int = 0

    def cards_by_stage(self) -> dict:
        """Returns {stage_id: [KanbanCard, ...]} mapping."""
        result = {s.id: [] for s in self.stages}
        for card in self.cards:
            if card.stage_id in result:
                result[card.stage_id].append(card)
            else:
                result[card.stage_id] = [card]
        return result

    def to_dict(self) -> dict:
        cards_by_stage = self.cards_by_stage()
        return {
            "total_cards": self.total_cards,
            "stages": [
                {
                    **s.to_dict(),
                    "cards": [c.to_dict() for c in cards_by_stage.get(s.id, [])],
                }
                for s in self.stages
            ],
        }
