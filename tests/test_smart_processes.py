"""
Unit tests for the Smart Processes bundle.
All API calls are mocked — no real HTTP requests made.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bundles.smart_processes.models import PipelineStage, SmartProcessType, SmartItem
from bundles.smart_processes.pipeline import Pipeline
from bundles.smart_processes.process import SmartProcess
from core.client import Bitrix24Client
from core.auth import WebhookAuth


def make_mock_client():
    auth = WebhookAuth(domain="example.bitrix24.com", user_id=1, token="testtoken")
    return Bitrix24Client(auth=auth)


class TestPipelineStage(unittest.TestCase):

    def test_from_api(self):
        data = {
            "id": "10",
            "title": "In Review",
            "sort": "30",
            "color": "#ff9900",
            "semantics": "WORK",
        }
        stage = PipelineStage.from_api(data)
        self.assertEqual(stage.id, 10)
        self.assertEqual(stage.title, "In Review")
        self.assertEqual(stage.sort, 30)
        self.assertEqual(stage.type, "WORK")

    def test_to_dict(self):
        stage = PipelineStage(id=1, title="New", sort=10, color="#ccc")
        d = stage.to_dict()
        self.assertEqual(d["id"], 1)
        self.assertEqual(d["title"], "New")


class TestSmartProcessType(unittest.TestCase):

    def test_from_api(self):
        data = {
            "id": 5,
            "entityTypeId": 128,
            "title": "Service Requests",
            "code": "SERVICE_REQ",
            "isStagesEnabled": True,
        }
        sp_type = SmartProcessType.from_api(data)
        self.assertEqual(sp_type.id, 5)
        self.assertEqual(sp_type.entity_type_id, 128)
        self.assertEqual(sp_type.title, "Service Requests")
        self.assertTrue(sp_type.is_use_kanban)


class TestSmartItem(unittest.TestCase):

    def test_from_api(self):
        data = {
            "id": 42,
            "title": "Fix printer",
            "stageId": "DT128_1:NEW",
            "assignedById": 1,
            "createdTime": "2026-03-06T10:00:00",
            "customField": "value",
        }
        item = SmartItem.from_api(data, entity_type_id=128)
        self.assertEqual(item.id, 42)
        self.assertEqual(item.title, "Fix printer")
        self.assertEqual(item.stage_id, "DT128_1:NEW")
        self.assertEqual(item.entity_type_id, 128)
        # Custom field captured
        self.assertIn("customField", item.fields)

    def test_to_dict(self):
        item = SmartItem(id=1, entity_type_id=128, title="Test", stage_id="NEW")
        d = item.to_dict()
        self.assertEqual(d["id"], 1)
        self.assertEqual(d["title"], "Test")
        self.assertEqual(d["stage_id"], "NEW")


class TestPipeline(unittest.TestCase):

    def setUp(self):
        self.client = make_mock_client()
        self.pipeline = Pipeline(self.client, entity_type_id=128)

    def test_get_stages_list(self):
        raw = [
            {"id": "1", "title": "New", "sort": "10", "color": "#ccc"},
            {"id": "2", "title": "Done", "sort": "40", "color": "#0f0"},
        ]
        with patch.object(self.pipeline._sp, "stage_list", return_value=raw):
            stages = self.pipeline.get_stages()
        self.assertEqual(len(stages), 2)
        self.assertEqual(stages[0].title, "New")

    def test_add_stage(self):
        with patch.object(self.pipeline._sp, "stage_add", return_value=5) as mock_add:
            stage = self.pipeline.add_stage("In Review", color="#ff0", sort=30, stage_type="WORK")
        mock_add.assert_called_once_with(128, {
            "title": "In Review",
            "color": "#ff0",
            "sort": 30,
            "semantics": "WORK",
        })
        self.assertEqual(stage.id, 5)

    def test_get_default_stages(self):
        stages = self.pipeline.get_default_stages()
        self.assertEqual(len(stages), 5)
        titles = [s["title"] for s in stages]
        self.assertIn("New", titles)
        self.assertIn("Done", titles)
        self.assertIn("Cancelled", titles)

    def test_initialize_default_pipeline(self):
        with patch.object(self.pipeline._sp, "stage_add", return_value=1):
            stages = self.pipeline.initialize_default_pipeline()
        self.assertEqual(len(stages), 5)


class TestSmartProcess(unittest.TestCase):

    def setUp(self):
        self.client = make_mock_client()
        self.sp = SmartProcess(self.client)

    def test_list_types(self):
        raw_types = [
            {"id": 1, "entityTypeId": 128, "title": "Service Requests"},
            {"id": 2, "entityTypeId": 130, "title": "HR Requests"},
        ]
        with patch.object(self.sp._sp, "type_list", return_value=raw_types):
            types = self.sp.list_types()
        self.assertEqual(len(types), 2)
        self.assertEqual(types[0].title, "Service Requests")

    def test_create_type(self):
        mock_result = {"type": {"id": 5, "entityTypeId": 128, "title": "Service Requests"}}
        with patch.object(self.sp._sp, "type_add", return_value=mock_result) as mock_add:
            sp_type = self.sp.create_type("Service Requests", code="SVC", use_kanban=True)
        mock_add.assert_called_once()
        self.assertEqual(sp_type.entity_type_id, 128)

    def test_add_item(self):
        mock_result = {"item": {
            "id": 42,
            "title": "Fix printer",
            "stageId": "DT128_1:NEW",
            "assignedById": 1,
        }}
        with patch.object(self.sp._sp, "item_add", return_value=mock_result) as mock_add:
            item = self.sp.add_item(
                entity_type_id=128,
                title="Fix printer",
                stage_id="DT128_1:NEW",
                assigned_by_id=1,
            )
        mock_add.assert_called_once_with(128, {
            "title": "Fix printer",
            "stageId": "DT128_1:NEW",
            "assignedById": 1,
        })
        self.assertEqual(item.id, 42)

    def test_move_item_to_stage(self):
        with patch.object(self.sp._sp, "item_update", return_value=True) as mock_update:
            result = self.sp.move_item_to_stage(
                item_id=42, entity_type_id=128, stage_id="DT128_1:IN_PROGRESS"
            )
        mock_update.assert_called_once_with(128, 42, {"stageId": "DT128_1:IN_PROGRESS"})
        self.assertTrue(result)

    def test_start_workflow(self):
        with patch.object(self.sp._bp, "workflow_start", return_value="wf-abc123") as mock_start:
            wf_id = self.sp.start_workflow(
                item_id=42, entity_type_id=128, template_id=5
            )
        mock_start.assert_called_once_with(
            5,
            ["crm", "CCrmDynamicType_128", "42"],
            None,
        )
        self.assertEqual(wf_id, "wf-abc123")

    def test_pause_workflow(self):
        with patch.object(self.sp._bp, "workflow_terminate", return_value=True) as mock_term:
            result = self.sp.pause_workflow("wf-abc123")
        mock_term.assert_called_once_with("wf-abc123", "paused")
        self.assertTrue(result)

    def test_stop_workflow(self):
        with patch.object(self.sp._bp, "workflow_terminate", return_value=True) as mock_term:
            result = self.sp.stop_workflow("wf-abc123")
        mock_term.assert_called_once_with("wf-abc123")
        self.assertTrue(result)

    def test_delete_workflow(self):
        with patch.object(self.sp._bp, "workflow_kill", return_value=True) as mock_kill:
            result = self.sp.delete_workflow("wf-abc123")
        mock_kill.assert_called_once_with("wf-abc123")
        self.assertTrue(result)

    def test_get_health_status_healthy(self):
        with patch.object(self.sp, "list_types", return_value=[MagicMock(), MagicMock()]):
            status = self.sp.get_health_status()
        self.assertEqual(status["status"], "healthy")
        self.assertEqual(status["metrics"]["type_count"], 2)

    def test_get_health_status_error(self):
        from core.exceptions import APIError
        with patch.object(self.sp, "list_types", side_effect=APIError("ERROR", "Test error")):
            status = self.sp.get_health_status()
        self.assertEqual(status["status"], "error")


if __name__ == "__main__":
    unittest.main()
