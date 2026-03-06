"""
Smart Processes Bundle — Mini-App for Bitrix24 Smart Process Automation

Smart Processes (Universal CRM Objects) bypass the standard CRM
lead/deal model, allowing custom business entities with:
- Custom fields and stages
- Automated pipelines
- Business process integration
- Kanban view in CRM

Features in this bundle:
- Smart process lifecycle management (create/configure/delete types)
- Item CRUD with stage transitions
- Pipeline stage management
- Use-case workflows for real company scenarios
- Liveness/health status reporting
"""

from .process import SmartProcess
from .pipeline import Pipeline
from .models import SmartProcessType, SmartItem, PipelineStage

__all__ = ["SmartProcess", "Pipeline", "SmartProcessType", "SmartItem", "PipelineStage"]
