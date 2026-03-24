"""Entrypoint for the local WATER prototype."""

from __future__ import annotations

import argparse

from allocator import allocate
from audit import AuditLogger
from prefect_translator import deploy_and_run
from registry import ResourceRegistry
from workflow_loader import load_workflow_from_yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run WATER workflow allocation/execution.")
    parser.add_argument(
        "--workflow",
        default="workflow.yaml",
        help="Path to workflow YAML file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logger = AuditLogger(db_path="audit.db")
    registry = ResourceRegistry()

    workflow = load_workflow_from_yaml(args.workflow)

    logger.append_event(action="SUBMITTED", workflow_name=workflow.name)
    print(f"Workflow submitted: {workflow.name}")

    target_node = allocate(workflow=workflow, registry=registry)
    if target_node is None:
        logger.append_event(action="FAILED", workflow_name=workflow.name)
        print("Allocation failed: no eligible node found.")
        return

    logger.append_event(
        action="ALLOCATED",
        workflow_name=workflow.name,
        target_node_id=target_node.node_id,
    )
    print(f"Allocated to node: {target_node.node_id}")

    logger.append_event(
        action="EXECUTED",
        workflow_name=workflow.name,
        target_node_id=target_node.node_id,
    )
    execution_success = deploy_and_run(workflow, target_node)
    if execution_success:
        logger.append_event(
            action="COMPLETED",
            workflow_name=workflow.name,
            target_node_id=target_node.node_id,
        )
        print("Workflow execution completed successfully.")
    else:
        logger.append_event(
            action="FAILED",
            workflow_name=workflow.name,
            target_node_id=target_node.node_id,
        )
        print("Workflow execution failed.")


if __name__ == "__main__":
    main()
