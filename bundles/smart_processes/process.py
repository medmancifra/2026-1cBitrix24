"""
SmartProcess — Core mini-app for Bitrix24 Smart Process management.

Implements full lifecycle management of Smart Process objects:
- Create/configure/delete Smart Process types
- CRUD for items within processes
- Stage transitions
- Business process integration
- Liveness status reporting for vitrine panel

Smart Processes bypass the traditional CRM Lead/Deal model,
giving full control over custom business entities.

Use-case example — Company service desk:
    sp = SmartProcess(client)
    # Create "Service Request" type
    svc_type = sp.create_type("Service Requests", code="SERVICE_REQ")
    # Add items
    sp.add_item(svc_type.entity_type_id, "Fix printer", stage="NEW")
    sp.add_item(svc_type.entity_type_id, "Setup laptop", stage="NEW")
    # Transition to next stage
    sp.move_item_to_stage(item_id=1, entity_type_id=128, stage="IN_PROGRESS")
"""

import datetime
import logging
from typing import Dict, List, Optional

from core.client import Bitrix24Client
from core.methods import SmartProcessMethods, BusinessProcessMethods
from core.exceptions import Bitrix24Error
from .models import SmartItem, SmartProcessType
from .pipeline import Pipeline

logger = logging.getLogger(__name__)


class SmartProcess:
    """
    Smart Process mini-app for Bitrix24.

    Provides high-level management of Smart Process types and their items,
    including pipeline stage management and business process automation.

    Usage:
        sp = SmartProcess(client)

        # List all smart process types
        types = sp.list_types()

        # Create a new type
        svc_type = sp.create_type("Service Requests", code="SERVICE_REQ")

        # Work with items
        item_id = sp.add_item(svc_type.entity_type_id, "Fix printer")
        sp.move_item_to_stage(item_id, svc_type.entity_type_id, stage_id="NEW")

        # Get full process state
        state = sp.get_process_state(svc_type.entity_type_id)
    """

    def __init__(self, client: Bitrix24Client):
        self.client = client
        self._sp = SmartProcessMethods(client)
        self._bp = BusinessProcessMethods(client)

    # ─── Type Management ───────────────────────────────────────────────────────

    def list_types(self) -> List[SmartProcessType]:
        """Returns all Smart Process types defined in the portal."""
        raw = self._sp.type_list()
        return [SmartProcessType.from_api(t) for t in raw]

    def create_type(
        self,
        title: str,
        code: str = "",
        use_kanban: bool = True,
        use_bp: bool = False,
    ) -> SmartProcessType:
        """
        Creates a new Smart Process type.

        Args:
            title: Display name (e.g. "Service Requests")
            code: Internal code for API identification
            use_kanban: Enable Kanban view in CRM
            use_bp: Enable Business Process integration

        Returns:
            Created SmartProcessType with entity_type_id
        """
        fields = {
            "title": title,
            "isStagesEnabled": use_kanban,
            "isUseInUserfieldEnabled": use_bp,
        }
        if code:
            fields["code"] = code

        result = self._sp.type_add(fields)
        if isinstance(result, dict):
            type_data = result.get("type", result)
            sp_type = SmartProcessType.from_api(type_data)
            logger.info("Created Smart Process type '%s' (entityTypeId=%d)",
                        title, sp_type.entity_type_id)
            return sp_type
        raise Bitrix24Error(f"Failed to create Smart Process type: {result}")

    def get_type(self, entity_type_id: int) -> SmartProcessType:
        """Returns a Smart Process type by its entity type ID."""
        result = self._sp.type_get(entity_type_id)
        if isinstance(result, dict):
            return SmartProcessType.from_api(result.get("type", result))
        raise Bitrix24Error(f"Smart Process type {entity_type_id} not found")

    def delete_type(self, entity_type_id: int) -> bool:
        """Deletes a Smart Process type and all its items."""
        return self._sp.type_delete(entity_type_id)

    # ─── Item Management ───────────────────────────────────────────────────────

    def add_item(
        self,
        entity_type_id: int,
        title: str,
        stage_id: Optional[str] = None,
        assigned_by_id: Optional[int] = None,
        extra_fields: Optional[Dict] = None,
    ) -> SmartItem:
        """
        Creates a new item in a Smart Process.

        Args:
            entity_type_id: The Smart Process type ID
            title: Item title
            stage_id: Initial stage ID (e.g. 'DT128_1:NEW')
            assigned_by_id: Assigned user ID
            extra_fields: Additional custom fields dict

        Returns:
            Created SmartItem
        """
        fields = {"title": title}
        if stage_id:
            fields["stageId"] = stage_id
        if assigned_by_id:
            fields["assignedById"] = assigned_by_id
        if extra_fields:
            fields.update(extra_fields)

        result = self._sp.item_add(entity_type_id, fields)
        if isinstance(result, dict):
            item_data = result.get("item", result)
            item = SmartItem.from_api(item_data, entity_type_id)
            logger.info("Created Smart Process item '%s' (ID=%d) in type %d",
                        title, item.id, entity_type_id)
            return item
        raise Bitrix24Error(f"Failed to create Smart Process item: {result}")

    def get_item(self, entity_type_id: int, item_id: int) -> SmartItem:
        """Gets a Smart Process item by ID."""
        result = self._sp.item_get(entity_type_id, item_id)
        if isinstance(result, dict):
            return SmartItem.from_api(result.get("item", result), entity_type_id)
        raise Bitrix24Error(f"Item {item_id} not found in type {entity_type_id}")

    def update_item(
        self,
        entity_type_id: int,
        item_id: int,
        fields: Dict,
    ) -> bool:
        """Updates a Smart Process item's fields."""
        return self._sp.item_update(entity_type_id, item_id, fields)

    def delete_item(self, entity_type_id: int, item_id: int) -> bool:
        """Deletes a Smart Process item."""
        return self._sp.item_delete(entity_type_id, item_id)

    def list_items(
        self,
        entity_type_id: int,
        stage_id: Optional[str] = None,
        assigned_by_id: Optional[int] = None,
    ) -> List[SmartItem]:
        """
        Lists items in a Smart Process with optional filtering.

        Args:
            entity_type_id: Smart Process type ID
            stage_id: Filter by stage
            assigned_by_id: Filter by assigned user

        Returns:
            List of SmartItem objects
        """
        filter_params = {}
        if stage_id:
            filter_params["stageId"] = stage_id
        if assigned_by_id:
            filter_params["assignedById"] = assigned_by_id

        raw = self._sp.item_list(entity_type_id, filter=filter_params)
        items_raw = raw
        if isinstance(raw, dict):
            items_raw = raw.get("items", [])
        return [SmartItem.from_api(i, entity_type_id) for i in items_raw]

    def move_item_to_stage(
        self,
        item_id: int,
        entity_type_id: int,
        stage_id: str,
    ) -> bool:
        """
        Moves an item to a different pipeline stage.

        This implements the core "operational business process chain"
        described in the issue — connecting items to chain operations,
        pausing, and stopping.

        Args:
            item_id: Item ID
            entity_type_id: Smart Process type ID
            stage_id: Target stage ID

        Returns:
            True if successful
        """
        result = self._sp.item_update(entity_type_id, item_id, {"stageId": stage_id})
        logger.info("Moved item %d to stage '%s'", item_id, stage_id)
        return result

    # ─── Business Process Integration ─────────────────────────────────────────

    def start_workflow(
        self,
        item_id: int,
        entity_type_id: int,
        template_id: int,
        parameters: Optional[Dict] = None,
    ) -> str:
        """
        Starts a business process workflow for a Smart Process item.

        Args:
            item_id: Smart Process item ID
            entity_type_id: Smart Process type ID
            template_id: BP template ID
            parameters: Workflow parameters

        Returns:
            Workflow instance ID
        """
        document_id = [
            "crm",
            f"CCrmDynamicType_{entity_type_id}",
            str(item_id),
        ]
        workflow_id = self._bp.workflow_start(template_id, document_id, parameters)
        logger.info("Started workflow %s for item %d (type %d)", workflow_id, item_id, entity_type_id)
        return workflow_id

    def pause_workflow(self, workflow_id: str) -> bool:
        """
        Pauses a running workflow (terminate with 'paused' status).
        Maps to the issue requirement: "остановка-пауза" (pause/stop).
        """
        return self._bp.workflow_terminate(workflow_id, "paused")

    def stop_workflow(self, workflow_id: str) -> bool:
        """
        Stops/terminates a running workflow.
        Maps to the issue requirement: "остановка" (stop).
        """
        return self._bp.workflow_terminate(workflow_id)

    def delete_workflow(self, workflow_id: str) -> bool:
        """
        Force-kills and removes a workflow instance.
        Maps to the issue requirement: "удаление" (delete).
        """
        return self._bp.workflow_kill(workflow_id)

    def list_workflows(self) -> List[dict]:
        """Lists all running business process workflows."""
        return self._bp.workflow_list()

    # ─── Process State & Health ────────────────────────────────────────────────

    def get_process_state(self, entity_type_id: int) -> dict:
        """
        Returns complete state of a Smart Process:
        - Pipeline stages with item counts
        - Running workflows
        - Summary metrics

        Used by the vitrine panel to display process status.
        """
        pipeline = Pipeline(self.client, entity_type_id)
        stages = pipeline.get_stages()
        items = self.list_items(entity_type_id)

        # Count items per stage
        stage_counts: Dict[str, int] = {}
        for item in items:
            if item.stage_id:
                stage_counts[item.stage_id] = stage_counts.get(item.stage_id, 0) + 1

        return {
            "entity_type_id": entity_type_id,
            "total_items": len(items),
            "stages": [
                {
                    **s.to_dict(),
                    "item_count": stage_counts.get(s.semantic_id or str(s.id), 0),
                }
                for s in stages
            ],
            "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    def get_health_status(self, entity_type_id: Optional[int] = None) -> dict:
        """
        Returns health/liveness status of the Smart Processes bundle.
        Used by the vitrine panel for status indicators.
        """
        try:
            types = self.list_types()
            status_data = {
                "bundle": "smart_processes",
                "status": "healthy",
                "metrics": {
                    "type_count": len(types),
                },
                "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            if entity_type_id:
                items = self.list_items(entity_type_id)
                status_data["metrics"]["item_count"] = len(items)
                status_data["entity_type_id"] = entity_type_id
            return status_data
        except Bitrix24Error as e:
            return {
                "bundle": "smart_processes",
                "status": "error",
                "error": str(e),
                "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
