"""
High-level wrappers for common Bitrix24 REST API methods.

Covers all major API categories from the developer documentation:
- Users
- CRM (deals, leads, contacts, companies)
- Tasks
- Smart Processes (universal CRM items)
- Business Processes
- Kanban / Task Stages

Each method corresponds directly to Bitrix24 REST API documentation.
"""

from typing import Any, Dict, List, Optional
from .client import Bitrix24Client


class UserMethods:
    """User management methods: user.*"""

    def __init__(self, client: Bitrix24Client):
        self._c = client

    def get(self, user_id: int) -> dict:
        """user.get — Get user by ID."""
        result = self._c.call("user.get", {"ID": user_id})
        if isinstance(result, list) and result:
            return result[0]
        return result

    def current(self) -> dict:
        """user.current — Get current authenticated user."""
        return self._c.call("user.current")

    def list(self, filter: dict = None, select: list = None) -> List[dict]:
        """user.get — List users with optional filter."""
        params = {}
        if filter:
            params["FILTER"] = filter
        if select:
            params["SELECT"] = select
        return self._c.get_all("user.get", params)

    def search(self, query: str) -> List[dict]:
        """user.search — Search users by name/email."""
        return self._c.call("user.search", {"FIND": query}) or []


class TaskMethods:
    """Task management methods: task.*"""

    def __init__(self, client: Bitrix24Client):
        self._c = client

    def add(self, fields: dict) -> int:
        """task.item.add — Create a new task. Returns task ID."""
        result = self._c.call("task.item.add", [fields])
        return int(result) if result else 0

    def get(self, task_id: int, fields: list = None) -> dict:
        """task.item.getdata — Get task by ID."""
        params = [task_id, fields or []]
        return self._c.call("task.item.getdata", params) or {}

    def update(self, task_id: int, fields: dict) -> bool:
        """task.item.update — Update task fields."""
        return self._c.call("task.item.update", [task_id, fields])

    def delete(self, task_id: int) -> bool:
        """task.item.delete — Delete a task."""
        return self._c.call("task.item.delete", [task_id])

    def list(self, filter: dict = None, select: list = None, order: dict = None) -> List[dict]:
        """task.item.list — List tasks with filter."""
        params = {
            "ORDER": order or {"ID": "DESC"},
            "FILTER": filter or {},
            "SELECT": select or ["ID", "TITLE", "STATUS", "RESPONSIBLE_ID", "DEADLINE"],
        }
        return self._c.get_all("task.item.list", params)

    def get_stages(self, entity_type: int = 1) -> List[dict]:
        """task.stages.get — Get Kanban/Planner stages."""
        return self._c.call("task.stages.get", {"entityType": entity_type}) or []

    def add_stage(self, fields: dict) -> int:
        """task.stages.add — Add a Kanban stage."""
        result = self._c.call("task.stages.add", fields)
        return int(result) if result else 0

    def update_stage(self, stage_id: int, fields: dict) -> bool:
        """task.stages.update — Update Kanban stage."""
        return self._c.call("task.stages.update", {"id": stage_id, **fields})

    def delete_stage(self, stage_id: int) -> bool:
        """task.stages.delete — Delete a Kanban stage."""
        return self._c.call("task.stages.delete", {"id": stage_id})

    def move_to_stage(self, task_id: int, stage_id: int) -> bool:
        """task.stages.movetask — Move task to a Kanban stage."""
        return self._c.call("task.stages.movetask", {"id": task_id, "stageId": stage_id})


class CRMMethods:
    """CRM methods: crm.*"""

    def __init__(self, client: Bitrix24Client):
        self._c = client

    # --- Deals ---
    def deal_add(self, fields: dict) -> int:
        """crm.deal.add — Create a deal. Returns deal ID."""
        result = self._c.call("crm.deal.add", {"fields": fields})
        return int(result) if result else 0

    def deal_get(self, deal_id: int) -> dict:
        """crm.deal.get — Get deal by ID."""
        return self._c.call("crm.deal.get", {"id": deal_id}) or {}

    def deal_update(self, deal_id: int, fields: dict) -> bool:
        """crm.deal.update — Update deal."""
        return self._c.call("crm.deal.update", {"id": deal_id, "fields": fields})

    def deal_delete(self, deal_id: int) -> bool:
        """crm.deal.delete — Delete deal."""
        return self._c.call("crm.deal.delete", {"id": deal_id})

    def deal_list(self, filter: dict = None, select: list = None, order: dict = None) -> List[dict]:
        """crm.deal.list — List deals."""
        params = {
            "order": order or {"DATE_CREATE": "DESC"},
            "filter": filter or {},
            "select": select or ["ID", "TITLE", "STAGE_ID", "ASSIGNED_BY_ID"],
        }
        return self._c.get_all("crm.deal.list", params)

    # --- Contacts ---
    def contact_add(self, fields: dict) -> int:
        """crm.contact.add — Create contact."""
        result = self._c.call("crm.contact.add", {"fields": fields})
        return int(result) if result else 0

    def contact_get(self, contact_id: int) -> dict:
        """crm.contact.get — Get contact by ID."""
        return self._c.call("crm.contact.get", {"id": contact_id}) or {}

    def contact_list(self, filter: dict = None, select: list = None) -> List[dict]:
        """crm.contact.list — List contacts."""
        params = {
            "filter": filter or {},
            "select": select or ["ID", "NAME", "LAST_NAME", "EMAIL", "PHONE"],
        }
        return self._c.get_all("crm.contact.list", params)

    # --- CRM Stages ---
    def stage_list(self, entity_type_id: int = 2) -> List[dict]:
        """crm.status.list — List CRM deal stages/statuses."""
        return self._c.call("crm.status.list", {"filter": {"ENTITY_ID": f"DEAL_STAGE"}}) or []


class SmartProcessMethods:
    """
    Smart Process (Universal CRM Objects) methods.
    Bypasses CRM lead/deal model — uses custom entity types.
    API: crm.type.*, crm.item.*
    """

    def __init__(self, client: Bitrix24Client):
        self._c = client

    # --- Smart Process Type Management ---
    def type_list(self) -> List[dict]:
        """crm.type.list — List all smart process types."""
        result = self._c.call("crm.type.list") or {}
        return result.get("types", []) if isinstance(result, dict) else result

    def type_add(self, fields: dict) -> dict:
        """crm.type.add — Create a new smart process type."""
        return self._c.call("crm.type.add", {"fields": fields}) or {}

    def type_get(self, entity_type_id: int) -> dict:
        """crm.type.get — Get smart process type by entityTypeId."""
        return self._c.call("crm.type.get", {"entityTypeId": entity_type_id}) or {}

    def type_update(self, entity_type_id: int, fields: dict) -> bool:
        """crm.type.update — Update smart process type."""
        return self._c.call("crm.type.update", {
            "entityTypeId": entity_type_id,
            "fields": fields,
        })

    def type_delete(self, entity_type_id: int) -> bool:
        """crm.type.delete — Delete smart process type."""
        return self._c.call("crm.type.delete", {"entityTypeId": entity_type_id})

    # --- Smart Process Items (Elements) ---
    def item_add(self, entity_type_id: int, fields: dict) -> dict:
        """crm.item.add — Create item in a smart process."""
        return self._c.call("crm.item.add", {
            "entityTypeId": entity_type_id,
            "fields": fields,
        }) or {}

    def item_get(self, entity_type_id: int, item_id: int) -> dict:
        """crm.item.get — Get smart process item."""
        return self._c.call("crm.item.get", {
            "entityTypeId": entity_type_id,
            "id": item_id,
        }) or {}

    def item_update(self, entity_type_id: int, item_id: int, fields: dict) -> bool:
        """crm.item.update — Update smart process item."""
        return self._c.call("crm.item.update", {
            "entityTypeId": entity_type_id,
            "id": item_id,
            "fields": fields,
        })

    def item_delete(self, entity_type_id: int, item_id: int) -> bool:
        """crm.item.delete — Delete smart process item."""
        return self._c.call("crm.item.delete", {
            "entityTypeId": entity_type_id,
            "id": item_id,
        })

    def item_list(
        self,
        entity_type_id: int,
        filter: dict = None,
        select: list = None,
        order: dict = None,
    ) -> List[dict]:
        """crm.item.list — List items in a smart process."""
        params = {
            "entityTypeId": entity_type_id,
            "order": order or {"id": "DESC"},
            "filter": filter or {},
            "select": select or ["id", "title", "stageId", "assignedById", "createdTime"],
        }
        return self._c.get_all("crm.item.list", params)

    def item_batch_import(self, entity_type_id: int, items: List[dict]) -> dict:
        """crm.item.batchImport — Bulk import items into smart process."""
        return self._c.call("crm.item.batchImport", {
            "entityTypeId": entity_type_id,
            "data": items,
        }) or {}

    # --- Stage Management for Smart Processes ---
    def stage_list(self, entity_type_id: int) -> List[dict]:
        """crm.status.list — Get stages for a smart process pipeline."""
        result = self._c.call("crm.item.stage.list", {
            "entityTypeId": entity_type_id,
        }) or {}
        return result.get("stages", []) if isinstance(result, dict) else result

    def stage_add(self, entity_type_id: int, fields: dict) -> int:
        """Add a stage to a smart process pipeline."""
        result = self._c.call("crm.item.stage.add", {
            "entityTypeId": entity_type_id,
            "fields": fields,
        })
        return int(result) if result else 0

    def stage_update(self, entity_type_id: int, stage_id: int, fields: dict) -> bool:
        """Update a smart process stage."""
        return self._c.call("crm.item.stage.update", {
            "entityTypeId": entity_type_id,
            "id": stage_id,
            "fields": fields,
        })

    def stage_delete(self, entity_type_id: int, stage_id: int) -> bool:
        """Delete a smart process stage."""
        return self._c.call("crm.item.stage.delete", {
            "entityTypeId": entity_type_id,
            "id": stage_id,
        })


class BusinessProcessMethods:
    """
    Business Process automation methods.
    bizproc.*, bp.*
    """

    def __init__(self, client: Bitrix24Client):
        self._c = client

    def workflow_list(self) -> List[dict]:
        """bizproc.workflow.instances.list — List running workflow instances."""
        return self._c.call("bizproc.workflow.instances.list") or []

    def workflow_start(self, template_id: int, document_id: list, parameters: dict = None) -> str:
        """bizproc.workflow.start — Start a business process workflow."""
        params = {
            "TEMPLATE_ID": template_id,
            "DOCUMENT_ID": document_id,
            "PARAMETERS": parameters or {},
        }
        return self._c.call("bizproc.workflow.start", params) or ""

    def workflow_terminate(self, workflow_id: str, status: str = "terminated") -> bool:
        """bizproc.workflow.terminate — Terminate a running workflow."""
        return self._c.call("bizproc.workflow.terminate", {
            "WORKFLOW_ID": workflow_id,
            "STATUS": status,
        })

    def workflow_kill(self, workflow_id: str) -> bool:
        """bizproc.workflow.kill — Force kill a workflow instance."""
        return self._c.call("bizproc.workflow.kill", {"WORKFLOW_ID": workflow_id})

    def template_list(self, filter: dict = None) -> List[dict]:
        """bizproc.workflow.template.list — List workflow templates."""
        return self._c.call("bizproc.workflow.template.list", {"filter": filter or {}}) or []

    def task_list(self, workflow_id: str = None) -> List[dict]:
        """bizproc.task.list — List pending workflow tasks."""
        params = {}
        if workflow_id:
            params["WORKFLOW_ID"] = workflow_id
        return self._c.call("bizproc.task.list", params) or []

    def task_complete(self, task_id: int, status: str, comment: str = "") -> bool:
        """bizproc.task.complete — Complete a workflow task."""
        return self._c.call("bizproc.task.complete", {
            "TASK_ID": task_id,
            "STATUS": status,
            "COMMENT": comment,
        })
