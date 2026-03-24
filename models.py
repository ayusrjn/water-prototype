"""Core data models for the WATER allocator prototype."""

from typing import Literal

from pydantic import BaseModel, validator


SensitivityLevel = Literal["public", "restricted", "hipaa"]
ExecutionMode = Literal["local", "ssh"]


class WATERWorkflow(BaseModel):
    """Represents a parsed workflow definition ready for allocation."""

    name: str
    docker_image: str
    entrypoint: str
    timeout_minutes: int
    requires_gpu: bool
    min_ram_gb: int
    input_path: str
    sensitivity: SensitivityLevel
    must_stay_local: bool
    target_node_id: str | None = None
    sync_input_to_remote: bool = False
    remote_input_path: str | None = None

    @validator("must_stay_local")
    def enforce_hipaa_locality(cls, must_stay_local: bool, values: dict) -> bool:
        """HIPAA workflows must remain local to edge infrastructure."""
        if values.get("sensitivity") == "hipaa" and not must_stay_local:
            msg = "HIPAA workflows must set must_stay_local=True."
            raise ValueError(msg)
        return must_stay_local


class ComputeNode(BaseModel):
    """Represents a candidate execution node in edge/cloud infrastructure."""

    node_id: str
    is_online: bool
    is_edge: bool
    max_sensitivity: SensitivityLevel
    has_gpu: bool
    available_ram_gb: int
    current_jobs: int
    max_jobs: int
    execution_mode: ExecutionMode = "local"
    ssh_host: str | None = None
    ssh_user: str | None = None
    ssh_key_path: str | None = None
