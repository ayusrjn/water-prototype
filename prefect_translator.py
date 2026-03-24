"""Translate WATER allocation decisions into Prefect execution calls."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from prefect import flow, get_run_logger, task

from models import ComputeNode, WATERWorkflow


@task(retries=1)
def run_docker_container(
    image: str,
    entrypoint: str,
    input_path: str,
    remote_input_path: str | None,
    timeout_minutes: int,
    sync_input_to_remote: bool,
    target_node: ComputeNode,
) -> bool:
    """Run a Docker container either locally or over SSH."""
    logger = get_run_logger()
    logger.info("Pulling image: %s", image)

    effective_input_path = input_path
    if target_node.execution_mode == "ssh" and remote_input_path:
        effective_input_path = remote_input_path

    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{effective_input_path}:/data/input:ro",
        image,
        "sh",
        "-lc",
        entrypoint,
    ]
    logger.info("Container command: %s", " ".join(shlex.quote(part) for part in docker_cmd))

    try:
        if target_node.execution_mode == "local":
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_minutes * 60,
                check=False,
            )
        elif target_node.execution_mode == "ssh":
            if not target_node.ssh_host or not target_node.ssh_user:
                logger.error("SSH node '%s' missing ssh_host/ssh_user.", target_node.node_id)
                return False

            ssh_base_cmd = ["ssh"]
            if target_node.ssh_key_path:
                ssh_base_cmd.extend(["-i", str(Path(target_node.ssh_key_path).expanduser())])
            ssh_base_cmd.append(f"{target_node.ssh_user}@{target_node.ssh_host}")

            if sync_input_to_remote:
                local_input = Path(input_path).expanduser()
                if not local_input.exists():
                    logger.error(
                        "Input path does not exist locally for sync: %s", local_input
                    )
                    return False

                remote_sync_path = remote_input_path or input_path
                remote_mkdir_cmd = ssh_base_cmd + [
                    f"mkdir -p {shlex.quote(remote_sync_path)}"
                ]
                mkdir_result = subprocess.run(
                    remote_mkdir_cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if mkdir_result.returncode != 0:
                    logger.error(
                        "Failed creating remote input directory: %s",
                        (mkdir_result.stderr or "").strip(),
                    )
                    return False

                rsync_cmd = [
                    "rsync",
                    "-az",
                    "--delete",
                    "-e",
                    " ".join(shlex.quote(x) for x in ssh_base_cmd[:-1]),
                    f"{str(local_input).rstrip('/')}/",
                    f"{ssh_base_cmd[-1]}:{remote_sync_path.rstrip('/')}/",
                ]
                logger.info("Syncing local input to remote node via rsync...")
                sync_result = subprocess.run(
                    rsync_cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if sync_result.returncode != 0:
                    logger.warning(
                        "Rsync sync failed, falling back to scp. stderr: %s",
                        (sync_result.stderr or "").strip(),
                    )
                    scp_cmd = ["scp", "-r"]
                    if target_node.ssh_key_path:
                        scp_cmd.extend(
                            ["-i", str(Path(target_node.ssh_key_path).expanduser())]
                        )
                    scp_cmd.extend(
                        [
                            f"{str(local_input).rstrip('/')}/.",
                            f"{target_node.ssh_user}@{target_node.ssh_host}:{remote_sync_path.rstrip('/')}/",
                        ]
                    )
                    scp_result = subprocess.run(
                        scp_cmd,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if scp_result.returncode != 0:
                        logger.error(
                            "Input sync failed via both rsync and scp. stderr: %s",
                            (scp_result.stderr or "").strip(),
                        )
                        return False

            quoted_remote_cmd = " ".join(shlex.quote(part) for part in docker_cmd)
            ssh_cmd = ssh_base_cmd.copy()
            ssh_cmd.append(quoted_remote_cmd)

            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_minutes * 60,
                check=False,
            )
        else:
            logger.error("Unsupported execution mode: %s", target_node.execution_mode)
            return False
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
    remote_input_path: str | None,
    timeout_minutes: int,
    sync_input_to_remote: bool,
    target_node: ComputeNode,
    target_node_id: str,
) -> bool:
    """Prefect flow representing execution of a WATER workflow."""
    logger = get_run_logger()
    logger.info(
        "Starting workflow '%s' execution on target node '%s'",
        workflow_name,
        target_node_id,
    )
    return run_docker_container(
        image=docker_image,
        entrypoint=entrypoint,
        input_path=input_path,
        remote_input_path=remote_input_path,
        timeout_minutes=timeout_minutes,
        sync_input_to_remote=sync_input_to_remote,
        target_node=target_node,
    )


def deploy_and_run(workflow: WATERWorkflow, target_node: ComputeNode) -> bool:
    """
    Execute an allocated workflow through Prefect.

    Returns:
        True if flow execution succeeds, otherwise False.
    """
    try:
        return bool(
            execute_water_workflow(
                workflow_name=workflow.name,
                docker_image=workflow.docker_image,
                entrypoint=workflow.entrypoint,
                input_path=workflow.input_path,
                remote_input_path=workflow.remote_input_path,
                timeout_minutes=workflow.timeout_minutes,
                sync_input_to_remote=workflow.sync_input_to_remote,
                target_node=target_node,
                target_node_id=target_node.node_id,
            )
        )
    except Exception:
        return False
