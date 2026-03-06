"""
KanbanBoard — Core Kanban mini-app for Bitrix24.

Manages Kanban columns (stages) and task cards using the Bitrix24
task.stages.* and task.item.* REST API methods.

Supports:
- Task Kanban (My Tasks / Group Tasks)
- Stage CRUD
- Card movement between stages
- Full board state retrieval
- Liveness/health status reporting
"""

import logging
from typing import Dict, List, Optional

from core.client import Bitrix24Client
from core.methods import TaskMethods
from core.exceptions import Bitrix24Error
from .models import KanbanStage, KanbanCard, BoardState

logger = logging.getLogger(__name__)


class KanbanBoard:
    """
    Kanban Board mini-app for Bitrix24.

    Manages Kanban stages and task cards. Works with both "My Tasks"
    (entity_type=1) and Group/Project tasks (entity_type=2).

    Usage:
        board = KanbanBoard(client, entity_type=1)
        state = board.get_board_state()
        for stage in state.stages:
            print(stage.title, len(state.cards_by_stage()[stage.id]))

        # Move card to another stage
        board.move_card(task_id=42, to_stage_id=5)

        # Add new stage
        board.add_stage("Review", color="#ff0000", sort=100)
    """

    def __init__(
        self,
        client: Bitrix24Client,
        entity_type: int = 1,
        group_id: Optional[int] = None,
    ):
        """
        Args:
            client: Authenticated Bitrix24Client
            entity_type: 1 = My Tasks Kanban, 2 = Group/Project Tasks Kanban
            group_id: Group ID for entity_type=2 boards
        """
        self.client = client
        self.entity_type = entity_type
        self.group_id = group_id
        self._tasks = TaskMethods(client)

    # ─── Stage Management ──────────────────────────────────────────────────────

    def get_stages(self) -> List[KanbanStage]:
        """Returns all stages (columns) for this Kanban board."""
        raw = self._tasks.get_stages(self.entity_type)
        stages = []
        if isinstance(raw, dict):
            # Response might be {stage_id: stage_data, ...}
            for stage_id, data in raw.items():
                if isinstance(data, dict):
                    data["ID"] = stage_id
                    stages.append(KanbanStage.from_api(data))
        elif isinstance(raw, list):
            stages = [KanbanStage.from_api(s) for s in raw]
        return sorted(stages, key=lambda s: s.sort)

    def add_stage(
        self,
        title: str,
        color: str = "",
        sort: int = 100,
        after_id: int = 0,
    ) -> KanbanStage:
        """
        Adds a new stage (column) to the Kanban board.

        Args:
            title: Stage name
            color: Hex color (e.g. '#ff9900')
            sort: Sort order (higher = further right)
            after_id: Place after this stage ID (0 = end)

        Returns:
            Created KanbanStage
        """
        fields = {
            "TITLE": title,
            "COLOR": color,
            "SORT": sort,
            "ENTITY_TYPE": self.entity_type,
        }
        if self.group_id:
            fields["ENTITY_ID"] = self.group_id
        if after_id:
            fields["AFTER_ID"] = after_id

        stage_id = self._tasks.add_stage(fields)
        logger.info("Created Kanban stage '%s' (ID=%d)", title, stage_id)
        return KanbanStage(
            id=stage_id,
            title=title,
            sort=sort,
            color=color,
            entity_type=self.entity_type,
        )

    def update_stage(
        self,
        stage_id: int,
        title: Optional[str] = None,
        color: Optional[str] = None,
        sort: Optional[int] = None,
    ) -> bool:
        """Updates an existing Kanban stage."""
        fields = {}
        if title is not None:
            fields["TITLE"] = title
        if color is not None:
            fields["COLOR"] = color
        if sort is not None:
            fields["SORT"] = sort
        return self._tasks.update_stage(stage_id, fields)

    def delete_stage(self, stage_id: int) -> bool:
        """Deletes a Kanban stage. Tasks in the stage are moved to the default stage."""
        return self._tasks.delete_stage(stage_id)

    # ─── Card Management ───────────────────────────────────────────────────────

    def get_cards(
        self,
        stage_id: Optional[int] = None,
        responsible_id: Optional[int] = None,
    ) -> List[KanbanCard]:
        """
        Returns cards (tasks) on this Kanban board.

        Args:
            stage_id: Filter by specific stage
            responsible_id: Filter by assigned user

        Returns:
            List of KanbanCard objects
        """
        filter_params = {}
        if stage_id is not None:
            filter_params["STAGE_ID"] = stage_id
        if responsible_id is not None:
            filter_params["RESPONSIBLE_ID"] = responsible_id
        if self.group_id:
            filter_params["GROUP_ID"] = self.group_id

        tasks = self._tasks.list(
            filter=filter_params,
            select=["ID", "TITLE", "STAGE_ID", "RESPONSIBLE_ID", "STATUS",
                    "DEADLINE", "GROUP_ID", "DESCRIPTION", "TAG", "CREATED_DATE"],
        )
        return [KanbanCard.from_task_api(t) for t in tasks]

    def add_card(
        self,
        title: str,
        stage_id: int,
        responsible_id: Optional[int] = None,
        deadline: Optional[str] = None,
        description: str = "",
        tags: List[str] = None,
    ) -> KanbanCard:
        """
        Creates a new card (task) on the Kanban board at the given stage.

        Args:
            title: Task title
            stage_id: Target Kanban stage ID
            responsible_id: Assigned user ID
            deadline: Deadline in ISO format (YYYY-MM-DD)
            description: Task description
            tags: List of tag strings

        Returns:
            Created KanbanCard
        """
        fields = {
            "TITLE": title,
            "STAGE_ID": stage_id,
            "DESCRIPTION": description,
        }
        if responsible_id:
            fields["RESPONSIBLE_ID"] = responsible_id
        if deadline:
            fields["DEADLINE"] = deadline
        if tags:
            fields["TAG"] = tags
        if self.group_id:
            fields["GROUP_ID"] = self.group_id

        task_id = self._tasks.add(fields)
        logger.info("Created Kanban card '%s' (ID=%d) in stage %d", title, task_id, stage_id)
        return KanbanCard(
            id=task_id,
            title=title,
            stage_id=stage_id,
            responsible_id=responsible_id,
            deadline=deadline,
            description=description,
            tags=tags or [],
        )

    def move_card(self, task_id: int, to_stage_id: int) -> bool:
        """
        Moves a card (task) to a different Kanban stage.

        Args:
            task_id: Task ID to move
            to_stage_id: Target stage ID

        Returns:
            True if successful
        """
        result = self._tasks.move_to_stage(task_id, to_stage_id)
        logger.info("Moved task %d to stage %d", task_id, to_stage_id)
        return result

    def update_card(self, task_id: int, **fields) -> bool:
        """Updates a card's fields."""
        return self._tasks.update(task_id, fields)

    def delete_card(self, task_id: int) -> bool:
        """Deletes a card (task) from the Kanban board."""
        return self._tasks.delete(task_id)

    # ─── Board State ───────────────────────────────────────────────────────────

    def get_board_state(self) -> BoardState:
        """
        Returns complete board state: all stages with their cards.

        This is used by the vitrine (showcase) panel to display
        the current Kanban board snapshot.

        Returns:
            BoardState with stages and cards
        """
        stages = self.get_stages()
        cards = self.get_cards()

        # Count cards per stage
        stage_counts: Dict[int, int] = {}
        for card in cards:
            stage_counts[card.stage_id] = stage_counts.get(card.stage_id, 0) + 1

        for stage in stages:
            stage.task_count = stage_counts.get(stage.id, 0)

        return BoardState(
            stages=stages,
            cards=cards,
            total_cards=len(cards),
        )

    def get_health_status(self) -> dict:
        """
        Returns health/liveness status of the Kanban bundle.

        Used by the vitrine panel to display bundle status indicators.

        Returns:
            Dict with status, metrics, and timestamp
        """
        import datetime
        try:
            stages = self.get_stages()
            cards = self.get_cards()
            return {
                "bundle": "kanban",
                "status": "healthy",
                "entity_type": self.entity_type,
                "group_id": self.group_id,
                "metrics": {
                    "stage_count": len(stages),
                    "card_count": len(cards),
                },
                "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
        except Bitrix24Error as e:
            return {
                "bundle": "kanban",
                "status": "error",
                "error": str(e),
                "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
