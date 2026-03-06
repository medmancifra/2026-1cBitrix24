"""
Unit tests for the Kanban bundle.
All API calls are mocked — no real HTTP requests made.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bundles.kanban.models import KanbanStage, KanbanCard, BoardState
from bundles.kanban.board import KanbanBoard
from core.client import Bitrix24Client
from core.auth import WebhookAuth


def make_mock_client():
    auth = WebhookAuth(domain="example.bitrix24.com", user_id=1, token="testtoken")
    client = Bitrix24Client(auth=auth)
    return client


class TestKanbanStage(unittest.TestCase):

    def test_from_api(self):
        data = {"ID": "5", "TITLE": "In Progress", "SORT": "20", "COLOR": "#ff0000", "ENTITY_TYPE": "1"}
        stage = KanbanStage.from_api(data)
        self.assertEqual(stage.id, 5)
        self.assertEqual(stage.title, "In Progress")
        self.assertEqual(stage.sort, 20)
        self.assertEqual(stage.color, "#ff0000")

    def test_to_dict(self):
        stage = KanbanStage(id=1, title="Backlog", sort=10, color="#ccc", entity_type=1, task_count=3)
        d = stage.to_dict()
        self.assertEqual(d["id"], 1)
        self.assertEqual(d["title"], "Backlog")
        self.assertEqual(d["task_count"], 3)


class TestKanbanCard(unittest.TestCase):

    def test_from_task_api(self):
        data = {
            "ID": "42",
            "TITLE": "Fix bug",
            "STAGE_ID": "5",
            "RESPONSIBLE_ID": "1",
            "STATUS": "3",
            "DEADLINE": "2026-03-31T00:00:00+00:00",
            "GROUP_ID": None,
            "DESCRIPTION": "Bug description",
            "TAG": ["bug", "urgent"],
            "CREATED_DATE": "2026-03-06T10:00:00+00:00",
        }
        card = KanbanCard.from_task_api(data)
        self.assertEqual(card.id, 42)
        self.assertEqual(card.title, "Fix bug")
        self.assertEqual(card.stage_id, 5)
        self.assertEqual(card.status, 3)
        self.assertEqual(card.tags, ["bug", "urgent"])

    def test_to_dict(self):
        card = KanbanCard(id=1, title="Task", stage_id=2, responsible_id=3)
        d = card.to_dict()
        self.assertEqual(d["id"], 1)
        self.assertEqual(d["stage_id"], 2)


class TestBoardState(unittest.TestCase):

    def test_cards_by_stage(self):
        stages = [
            KanbanStage(id=1, title="Backlog", sort=10),
            KanbanStage(id=2, title="In Progress", sort=20),
        ]
        cards = [
            KanbanCard(id=10, title="T1", stage_id=1),
            KanbanCard(id=11, title="T2", stage_id=1),
            KanbanCard(id=12, title="T3", stage_id=2),
        ]
        board = BoardState(stages=stages, cards=cards, total_cards=3)
        by_stage = board.cards_by_stage()

        self.assertEqual(len(by_stage[1]), 2)
        self.assertEqual(len(by_stage[2]), 1)

    def test_to_dict(self):
        stages = [KanbanStage(id=1, title="Backlog", sort=10)]
        cards = [KanbanCard(id=10, title="T1", stage_id=1)]
        board = BoardState(stages=stages, cards=cards, total_cards=1)
        d = board.to_dict()

        self.assertEqual(d["total_cards"], 1)
        self.assertEqual(len(d["stages"]), 1)
        self.assertEqual(d["stages"][0]["title"], "Backlog")
        self.assertEqual(len(d["stages"][0]["cards"]), 1)


class TestKanbanBoard(unittest.TestCase):

    def setUp(self):
        self.client = make_mock_client()
        self.board = KanbanBoard(self.client, entity_type=1)

    def test_get_stages_dict_format(self):
        raw_stages = {
            "5": {"TITLE": "Backlog", "SORT": "10", "COLOR": "#ccc", "ENTITY_TYPE": "1"},
            "6": {"TITLE": "Done", "SORT": "50", "COLOR": "#0f0", "ENTITY_TYPE": "1"},
        }
        with patch.object(self.board._tasks, "get_stages", return_value=raw_stages):
            stages = self.board.get_stages()
        self.assertEqual(len(stages), 2)
        # Should be sorted by sort order
        self.assertEqual(stages[0].title, "Backlog")
        self.assertEqual(stages[1].title, "Done")

    def test_get_stages_list_format(self):
        raw_stages = [
            {"ID": "5", "TITLE": "Backlog", "SORT": "10", "COLOR": "#ccc"},
            {"ID": "6", "TITLE": "Done", "SORT": "50", "COLOR": "#0f0"},
        ]
        with patch.object(self.board._tasks, "get_stages", return_value=raw_stages):
            stages = self.board.get_stages()
        self.assertEqual(len(stages), 2)

    def test_add_stage(self):
        with patch.object(self.board._tasks, "add_stage", return_value=10) as mock_add:
            stage = self.board.add_stage("Review", color="#ff9900", sort=30)
        mock_add.assert_called_once()
        self.assertEqual(stage.id, 10)
        self.assertEqual(stage.title, "Review")
        self.assertEqual(stage.color, "#ff9900")

    def test_move_card(self):
        with patch.object(self.board._tasks, "move_to_stage", return_value=True) as mock_move:
            result = self.board.move_card(task_id=42, to_stage_id=5)
        mock_move.assert_called_once_with(42, 5)
        self.assertTrue(result)

    def test_add_card(self):
        with patch.object(self.board._tasks, "add", return_value=99) as mock_add:
            card = self.board.add_card(
                title="New Task",
                stage_id=5,
                responsible_id=1,
                deadline="2026-12-31",
            )
        mock_add.assert_called_once()
        self.assertEqual(card.id, 99)
        self.assertEqual(card.title, "New Task")
        self.assertEqual(card.stage_id, 5)

    def test_get_board_state(self):
        mock_stages = [KanbanStage(id=1, title="Backlog", sort=10)]
        mock_cards = [
            KanbanCard(id=10, title="T1", stage_id=1),
            KanbanCard(id=11, title="T2", stage_id=1),
        ]
        with patch.object(self.board, "get_stages", return_value=mock_stages), \
             patch.object(self.board, "get_cards", return_value=mock_cards):
            state = self.board.get_board_state()

        self.assertEqual(state.total_cards, 2)
        self.assertEqual(state.stages[0].task_count, 2)

    def test_get_health_status_healthy(self):
        with patch.object(self.board, "get_stages", return_value=[]), \
             patch.object(self.board, "get_cards", return_value=[]):
            status = self.board.get_health_status()
        self.assertEqual(status["status"], "healthy")
        self.assertEqual(status["bundle"], "kanban")

    def test_get_health_status_error(self):
        from core.exceptions import APIError
        with patch.object(self.board, "get_stages", side_effect=APIError("ERROR", "Test error")):
            status = self.board.get_health_status()
        self.assertEqual(status["status"], "error")
        self.assertIn("error", status)


if __name__ == "__main__":
    unittest.main()
