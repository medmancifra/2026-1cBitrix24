#!/usr/bin/env python3
"""
Service Desk Use-Case Example
==============================
Demonstrates real-world usage of the Bitrix24 boilerplate for a company
service desk workflow using Smart Processes + Business Processes.

This example shows:
1. Creating a Smart Process type for service requests
2. Initializing a default pipeline
3. Creating service request items
4. Moving items through the pipeline
5. Launching and managing business process workflows

IMPORTANT: This script makes REAL API calls to Bitrix24.
           Set BX24_DOMAIN and BX24_WEBHOOK_TOKEN before running.

Usage:
    export BX24_DOMAIN="your-portal.bitrix24.com"
    export BX24_WEBHOOK_TOKEN="your_token"
    python examples/service_desk_usecase.py
"""

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("service_desk_example")


def main():
    from core import Bitrix24Client
    from bundles.smart_processes import SmartProcess
    from bundles.smart_processes.pipeline import Pipeline

    log.info("Connecting to Bitrix24...")
    client = Bitrix24Client.from_env()

    sp = SmartProcess(client)

    # ── Step 1: Check or create Smart Process type ────────────────────────────
    log.info("Checking existing smart process types...")
    types = sp.list_types()

    svc_type = None
    for t in types:
        if t.code == "SERVICE_DESK_DEMO" or "Service Desk Demo" in t.title:
            svc_type = t
            log.info("Found existing type: %s (entityTypeId=%d)", t.title, t.entity_type_id)
            break

    if not svc_type:
        log.info("Creating 'Service Desk Demo' smart process type...")
        svc_type = sp.create_type(
            title="Service Desk Demo",
            code="SERVICE_DESK_DEMO",
            use_kanban=True,
            use_bp=False,
        )
        log.info("Created: entityTypeId=%d", svc_type.entity_type_id)

    # ── Step 2: Initialize pipeline ───────────────────────────────────────────
    pipeline = Pipeline(client, entity_type_id=svc_type.entity_type_id)
    stages = pipeline.get_stages()

    if not stages:
        log.info("Initializing default pipeline (5 stages)...")
        stages = pipeline.initialize_default_pipeline()
        log.info("Pipeline stages created: %s", [s.title for s in stages])
    else:
        log.info("Pipeline already has %d stages: %s",
                 len(stages), [s.title for s in stages])

    first_stage = stages[0] if stages else None

    # ── Step 3: Create service request items ─────────────────────────────────
    log.info("Creating service request items...")
    service_requests = [
        "Fix printer in Office 301",
        "Setup laptop for new employee: John Doe",
        "Restore access to corporate email for Ivan Petrov",
        "Install VPN client on marketing team MacBooks",
    ]

    created_items = []
    for title in service_requests:
        try:
            item = sp.add_item(
                entity_type_id=svc_type.entity_type_id,
                title=title,
                stage_id=first_stage.semantic_id if first_stage else None,
            )
            created_items.append(item)
            log.info("  [+] Created #%d: %s", item.id, title)
        except Exception as e:
            log.warning("  [!] Failed to create '%s': %s", title, e)

    # ── Step 4: Move first item to "In Progress" ──────────────────────────────
    if created_items and len(stages) >= 2:
        item = created_items[0]
        next_stage = stages[1]
        log.info("Moving item #%d to stage '%s'...", item.id, next_stage.title)
        try:
            sp.move_item_to_stage(
                item_id=item.id,
                entity_type_id=svc_type.entity_type_id,
                stage_id=next_stage.semantic_id or str(next_stage.id),
            )
            log.info("  [+] Moved to '%s'", next_stage.title)
        except Exception as e:
            log.warning("  [!] Failed to move: %s", e)

    # ── Step 5: Display board state ───────────────────────────────────────────
    log.info("\n=== Current Process State ===")
    try:
        state = sp.get_process_state(svc_type.entity_type_id)
        log.info("Total items: %d", state["total_items"])
        for stage in state["stages"]:
            log.info("  %-20s: %d items", stage["title"], stage["item_count"])
    except Exception as e:
        log.warning("Could not get process state: %s", e)

    # ── Step 6: Health status ─────────────────────────────────────────────────
    log.info("\n=== Bundle Health Status ===")
    health = sp.get_health_status(entity_type_id=svc_type.entity_type_id)
    log.info("Status: %s", health["status"])
    log.info("Metrics: %s", health.get("metrics", {}))

    log.info("\n=== Service Desk Use-Case Complete ===")
    log.info("Entity Type ID: %d", svc_type.entity_type_id)
    log.info("Items created: %d", len(created_items))
    log.info(
        "To view via CLI: python cli/main.py smart list --type-id %d",
        svc_type.entity_type_id
    )


if __name__ == "__main__":
    main()
