"""Translate WATER allocation decisions into Prefect execution calls via remote Workers."""

from __future__ import annotations

import shlex
import subprocess
from prefect import flow, get_run_logger, task
from prefect.deployments import run_deployment

from models import ComputeNode, WATERWorkflow


@task(retries=1)
def run_docker_container(
    image: str,
    entrypoint: str,
    input_path: str,
    timeout_minutes: int,
) -> bool:
    """Run a Docker container locally on whichever node the Prefect Worker is deployed."""
    logger = get_run_logger()
    logger.info("Pulling image: %s", image)

    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{input_path}:/data/input:ro",
        image, "sh", "-lc", entrypoint,
    ]
    logger.info("Container command: %s", " ".join(shlex.quote(part) for part in docker_cmd))

    try:
        # Run docker on the physical machine providing the worker
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout_minutes * 60,
            check=False,
        )
    except subprocess.TimeoutExpired:
        logger.error("Execution timed out after %s minutes.", timeout_minutes)
        return False
    except Exception as exc:
        logger.exception("Execution failed: %s", exc)
        return False

    if result.stdout:
        logger.info("stdout:\n%s", result.stdout.strip())
    if result.stderr:
        logger.warning("stderr:\n%s", result.stderr.strip())

    success = result.returncode == 0
    if not success:
        logger.error("Container execution failed with code %s", result.returncode)
    return success


@flow(name="WATER_Execution_Flow")
def execute_water_workflow(
    workflow_name: str,
    docker_image: str,
    entrypoint: str,
    input_path: str,
    timeout_minutes: int,
) -> bool:
    """Prefect flow representing execution of a WATER workflow on a worker node."""
    logger = get_run_logger()
    logger.info("Starting workflow '%s' execution", workflow_name)
    return run_docker_container(
        image=docker_image,
        entrypoint=entrypoint,
        input_path=input_path,
        timeout_minutes=timeout_minutes,
    )


def deploy_and_run(workflow: WATERWorkflow, target_node: ComputeNode) -> bool:
    """
    Dispatch the allocated workflow to the specific compute node's Prefect Deployment.

    Returns:
        True if flow execution succeeds, otherwise False.
    """
    if workflow.sync_input_to_remote:
        print("WARNING: Data synchronization over SSH is disabled in the LAN Distributed architecture.")
        print("Please ensure your nodes share a network drive or sync data via another mechanism.")

    # In LAN distributed architecture, each node runs a unique served deployment named after its ID.
    deployment_name = f"WATER_Execution_Flow/{target_node.node_id}_deployment"
    
    try:
        print(f"Submitting workload to Prefect deployment: {deployment_name}...")
        
        # run_deployment triggers the remote worker serving this deployment
        flow_run = run_deployment(
            name=deployment_name,
            parameters={
                "workflow_name": workflow.name,
                "docker_image": workflow.docker_image,
                "entrypoint": workflow.entrypoint,
                "input_path": workflow.input_path,
                "timeout_minutes": workflow.timeout_minutes,
            },
            timeout=0  # Wait for completion
        )
        return flow_run.state.is_completed()
    except Exception as e:
        print(f"Failed to submit or execute flow on {deployment_name}: {e}")
        return False
