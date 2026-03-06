"""
Data models for the Smart Processes bundle.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PipelineStage:
    """A stage in a Smart Process pipeline (Kanban column in CRM)."""
    id: int
    title: str
    sort: int = 100
    color: str = "#00b4e3"
    type: str = "WORK"  # WORK, SUCCESS, FAIL
    entity_type_id: int = 0
    semantic_id: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict) -> "PipelineStage":
        return cls(
            id=int(data.get("id", data.get("ID", 0))),
            title=data.get("title", data.get("NAME", data.get("TITLE", ""))),
            sort=int(data.get("sort", data.get("SORT", 100))),
            color=data.get("color", data.get("COLOR", "#00b4e3")),
            type=data.get("semantics", data.get("SEMANTICS", "WORK")),
            entity_type_id=int(data.get("entityTypeId", 0)),
            semantic_id=data.get("statusId", data.get("STATUS_ID")),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "sort": self.sort,
            "color": self.color,
            "type": self.type,
            "entity_type_id": self.entity_type_id,
            "semantic_id": self.semantic_id,
        }


@dataclass
class SmartProcessType:
    """A Smart Process type definition (the entity type, like 'ServiceRequest')."""
    id: int
    entity_type_id: int
    title: str
    code: str = ""
    created_by: Optional[int] = None
    is_use_in_bp: bool = False
    is_use_kanban: bool = True
    relations: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: dict) -> "SmartProcessType":
        return cls(
            id=int(data.get("id", 0)),
            entity_type_id=int(data.get("entityTypeId", 0)),
            title=data.get("title", ""),
            code=data.get("code", ""),
            created_by=data.get("createdBy"),
            is_use_in_bp=bool(data.get("isUseInUserfieldEnabled", False)),
            is_use_kanban=bool(data.get("isStagesEnabled", True)),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "entity_type_id": self.entity_type_id,
            "title": self.title,
            "code": self.code,
            "is_use_in_bp": self.is_use_in_bp,
            "is_use_kanban": self.is_use_kanban,
        }


@dataclass
class SmartItem:
    """An item (record) within a Smart Process type."""
    id: int
    entity_type_id: int
    title: str
    stage_id: Optional[str] = None
    assigned_by_id: Optional[int] = None
    created_time: Optional[str] = None
    updated_time: Optional[str] = None
    opened: bool = True
    fields: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: dict, entity_type_id: int = 0) -> "SmartItem":
        item = cls(
            id=int(data.get("id", 0)),
            entity_type_id=entity_type_id or int(data.get("entityTypeId", 0)),
            title=data.get("title", ""),
            stage_id=data.get("stageId"),
            assigned_by_id=data.get("assignedById"),
            created_time=data.get("createdTime"),
            updated_time=data.get("updatedTime"),
            opened=bool(data.get("opened", True)),
        )
        # Capture all extra fields
        known = {"id", "entityTypeId", "title", "stageId", "assignedById",
                 "createdTime", "updatedTime", "opened"}
        item.fields = {k: v for k, v in data.items() if k not in known}
        return item

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "entity_type_id": self.entity_type_id,
            "title": self.title,
            "stage_id": self.stage_id,
            "assigned_by_id": self.assigned_by_id,
            "created_time": self.created_time,
            "updated_time": self.updated_time,
            "opened": self.opened,
            **self.fields,
        }
