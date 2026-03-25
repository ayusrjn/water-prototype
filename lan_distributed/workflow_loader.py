"""Load WATER workflow definitions from YAML files."""

from __future__ import annotations

from pathlib import Path

import yaml

from models import WATERWorkflow


def load_workflow_from_yaml(path: str | Path) -> WATERWorkflow:
    """Parse a nested workflow YAML file into a WATERWorkflow model."""
    yaml_path = Path(path)
    with yaml_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    execution = config.get("execution", {})
    resources = config.get("resources", {})
    data = config.get("data", {})
    placement = config.get("placement", {})
    transfer = config.get("transfer", {})

    return WATERWorkflow(
        name=config.get("name"),
        docker_image=execution.get("docker_image"),
        entrypoint=execution.get("entrypoint"),
        timeout_minutes=execution.get("timeout_minutes"),
        requires_gpu=resources.get("requires_gpu"),
        min_ram_gb=resources.get("min_ram_gb"),
        input_path=data.get("input_path"),
        sensitivity=data.get("sensitivity"),
        must_stay_local=data.get("must_stay_local"),
        target_node_id=placement.get("target_node_id"),
        sync_input_to_remote=bool(transfer.get("sync_input_to_remote", False)),
        remote_input_path=transfer.get("remote_input_path"),
    )
