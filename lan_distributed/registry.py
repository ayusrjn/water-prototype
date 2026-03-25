"""In-memory resource registry for WATER prototype."""

from __future__ import annotations

import os

from models import ComputeNode


class ResourceRegistry:
    """Mock registry that holds the current view of available compute nodes."""

    def __init__(self) -> None:
        gcp_host = os.getenv("WATER_GCP_HOST", "34.0.0.10")
        gcp_user = os.getenv("WATER_GCP_USER", "ubuntu")
        gcp_key_path = os.getenv("WATER_GCP_KEY_PATH", "~/.ssh/gcp-water.pem")

        self.nodes: list[ComputeNode] = [
            ComputeNode(
                node_id="laptop-edge",
                is_online=True,
                is_edge=True,
                max_sensitivity="hipaa",
                has_gpu=True,
                available_ram_gb=16,
                current_jobs=0,
                max_jobs=4,
                execution_mode="local",
            ),
            ComputeNode(
                node_id="laptop-edge-2",
                is_online=True,
                is_edge=True,
                max_sensitivity="hipaa",
                has_gpu=False,
                available_ram_gb=8,
                current_jobs=0,
                max_jobs=4,
                execution_mode="local",
            ),
            ComputeNode(
                node_id="laptop-edge-3",
                is_online=True,
                is_edge=True,
                max_sensitivity="hipaa",
                has_gpu=False,
                available_ram_gb=8,
                current_jobs=0,
                max_jobs=4,
                execution_mode="local",
            ),
            ComputeNode(
                node_id="gcp-edge",
                is_online=True,
                is_edge=False,
                max_sensitivity="restricted",
                has_gpu=False,
                available_ram_gb=32,
                current_jobs=0,
                max_jobs=8,
                execution_mode="ssh",
                ssh_host=gcp_host,
                ssh_user=gcp_user,
                ssh_key_path=gcp_key_path,
            ),
            ComputeNode(
                node_id="edge-offline-01",
                is_online=False,
                is_edge=True,
                max_sensitivity="restricted",
                has_gpu=True,
                available_ram_gb=16,
                current_jobs=0,
                max_jobs=2,
            ),
        ]

    def get_nodes(self) -> list[ComputeNode]:
        """Return a copy of nodes to prevent accidental external mutation."""
        return list(self.nodes)
