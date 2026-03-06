"""
Pipeline — Stage management for Smart Process workflows.

A Pipeline represents the sequence of stages (Kanban columns in CRM)
for a specific Smart Process entity type.
"""

import logging
from typing import List, Optional

from core.client import Bitrix24Client
from core.methods import SmartProcessMethods
from .models import PipelineStage

logger = logging.getLogger(__name__)


class Pipeline:
    """
    Manages stages (pipeline) for a Smart Process.

    In Bitrix24, each Smart Process type has its own set of stages
    that function as Kanban columns in the CRM interface.

    Usage:
        pipeline = Pipeline(client, entity_type_id=128)
        stages = pipeline.get_stages()
        pipeline.add_stage("In Review", color="#ffcc00", sort=200)
        pipeline.move_item(item_id=1, to_stage="DT128_2:IN")
    """

    def __init__(self, client: Bitrix24Client, entity_type_id: int):
        self.client = client
        self.entity_type_id = entity_type_id
        self._sp = SmartProcessMethods(client)

    def get_stages(self) -> List[PipelineStage]:
        """Returns all stages for this pipeline, sorted by sort order."""
        raw = self._sp.stage_list(self.entity_type_id)
        stages = []
        if isinstance(raw, list):
            stages = [PipelineStage.from_api(s) for s in raw]
        elif isinstance(raw, dict):
            for stage_id, data in raw.items():
                if isinstance(data, dict):
                    data["id"] = stage_id
                    stages.append(PipelineStage.from_api(data))
        return sorted(stages, key=lambda s: s.sort)

    def add_stage(
        self,
        title: str,
        color: str = "#00b4e3",
        sort: int = 100,
        stage_type: str = "WORK",  # WORK, SUCCESS, FAIL
    ) -> PipelineStage:
        """
        Adds a new stage to the pipeline.

        Args:
            title: Stage name
            color: Hex color code
            sort: Sort order (ascending)
            stage_type: 'WORK' (in progress), 'SUCCESS' (won/done), 'FAIL' (lost)

        Returns:
            Created PipelineStage
        """
        fields = {
            "title": title,
            "color": color,
            "sort": sort,
            "semantics": stage_type,
        }
        stage_id = self._sp.stage_add(self.entity_type_id, fields)
        logger.info("Added pipeline stage '%s' (ID=%d) to type %d",
                    title, stage_id, self.entity_type_id)
        return PipelineStage(
            id=stage_id,
            title=title,
            sort=sort,
            color=color,
            type=stage_type,
            entity_type_id=self.entity_type_id,
        )

    def update_stage(
        self,
        stage_id: int,
        title: Optional[str] = None,
        color: Optional[str] = None,
        sort: Optional[int] = None,
    ) -> bool:
        """Updates pipeline stage properties."""
        fields = {}
        if title is not None:
            fields["title"] = title
        if color is not None:
            fields["color"] = color
        if sort is not None:
            fields["sort"] = sort
        return self._sp.stage_update(self.entity_type_id, stage_id, fields)

    def delete_stage(self, stage_id: int) -> bool:
        """Deletes a pipeline stage. Items move to the first stage."""
        return self._sp.stage_delete(self.entity_type_id, stage_id)

    def get_default_stages(self) -> List[dict]:
        """
        Returns a default set of stages suitable for most business workflows.
        Can be used to initialize a new pipeline quickly.
        """
        return [
            {"title": "New", "color": "#bdbdbd", "sort": 10, "type": "WORK"},
            {"title": "In Progress", "color": "#47aef5", "sort": 20, "type": "WORK"},
            {"title": "In Review", "color": "#fd913a", "sort": 30, "type": "WORK"},
            {"title": "Done", "color": "#7fc942", "sort": 40, "type": "SUCCESS"},
            {"title": "Cancelled", "color": "#fc7e69", "sort": 50, "type": "FAIL"},
        ]

    def initialize_default_pipeline(self) -> List[PipelineStage]:
        """
        Creates a default set of stages for a new pipeline.
        Useful for initializing a fresh Smart Process type.
        """
        created = []
        for s in self.get_default_stages():
            stage = self.add_stage(s["title"], s["color"], s["sort"], s["type"])
            created.append(stage)
        logger.info("Initialized default pipeline with %d stages", len(created))
        return created
