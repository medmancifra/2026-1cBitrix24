#!/usr/bin/env python3
"""
Kanban Board Example
====================
Demonstrates usage of the Kanban bundle for task management.

Shows:
1. Getting Kanban board state
2. Creating stages
3. Creating and moving cards
4. Getting health status

Usage:
    export BX24_DOMAIN=... BX24_WEBHOOK_TOKEN=...
    python examples/kanban_example.py
"""

import os
import sys
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("kanban_example")


def main():
    from core import Bitrix24Client
    from bundles.kanban import KanbanBoard

    log.info("Connecting to Bitrix24...")
    client = Bitrix24Client.from_env()

    # My Tasks Kanban board
    board = KanbanBoard(client, entity_type=1)

    # ── Get board state ───────────────────────────────────────────────────────
    log.info("Loading Kanban board state...")
    state = board.get_board_state()

    log.info("\n=== Kanban Board State ===")
    log.info("Total cards: %d", state.total_cards)
    cards_by_stage = state.cards_by_stage()

    for stage in state.stages:
        cards = cards_by_stage.get(stage.id, [])
        log.info("  [%s] %s: %d cards", stage.color or "#ccc", stage.title, len(cards))
        for card in cards[:3]:  # Show first 3 cards per stage
            log.info("    - #%d: %s (resp: %s)", card.id, card.title, card.responsible_id)

    # ── Print as JSON ─────────────────────────────────────────────────────────
    log.info("\n=== Board JSON (first 100 chars per stage) ===")
    board_dict = state.to_dict()
    for stage in board_dict["stages"]:
        print(f"  Stage: {stage['title']} ({stage['task_count']} cards)")

    # ── Health status ─────────────────────────────────────────────────────────
    log.info("\n=== Kanban Health Status ===")
    health = board.get_health_status()
    print(json.dumps(health, indent=2, default=str))


if __name__ == "__main__":
    main()
