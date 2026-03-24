"""Constraint-aware allocator for WATER workflows."""

from __future__ import annotations

from models import ComputeNode, WATERWorkflow
from registry import ResourceRegistry


SENSITIVITY_RANK = {"public": 0, "restricted": 1, "hipaa": 2}
EDGE_PREFERENCE_BONUS = 50


def _is_sensitivity_eligible(node: ComputeNode, workflow: WATERWorkflow) -> bool:
    return (
        SENSITIVITY_RANK[node.max_sensitivity]
        >= SENSITIVITY_RANK[workflow.sensitivity]
    )


def _passes_hard_constraints(node: ComputeNode, workflow: WATERWorkflow) -> bool:
    if workflow.target_node_id and node.node_id != workflow.target_node_id:
        return False
    if not node.is_online:
        return False
    if not _is_sensitivity_eligible(node, workflow):
        return False
    if workflow.requires_gpu and not node.has_gpu:
        return False
    if node.available_ram_gb < workflow.min_ram_gb:
        return False
    if node.current_jobs >= node.max_jobs:
        return False
    if workflow.must_stay_local and not node.is_edge:
        return False
    return True


def _score_node(node: ComputeNode) -> int:
    score = node.available_ram_gb
    if node.is_edge:
        score += EDGE_PREFERENCE_BONUS
    return score


def allocate(workflow: WATERWorkflow, registry: ResourceRegistry) -> ComputeNode | None:
    """
    Allocate a workflow to the best eligible node.

    Returns:
        ComputeNode if allocation is possible, otherwise None.
    """
    eligible_nodes = [
        node for node in registry.get_nodes() if _passes_hard_constraints(node, workflow)
    ]
    if not eligible_nodes:
        return None

    return max(eligible_nodes, key=_score_node)
