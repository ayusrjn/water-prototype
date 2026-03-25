"""Script to launch a Prefect Worker for a specific edge node."""

import argparse
from prefect_translator import execute_water_workflow

def parse_args():
    parser = argparse.ArgumentParser(description="Start a WATER compute node worker.")
    parser.add_argument("--node-id", required=True, help="The ID of this compute node (e.g. laptop-edge, gcp-edge).")
    return parser.parse_args()

def main():
    args = parse_args()
    print(f"Starting Prefect Worker for node: {args.node_id}")
    print(f"This machine is now serving deployment `{args.node_id}_deployment`.")

    # Serving the flow turns this script into a dedicated worker. 
    # It continuously connects to the Prefect server waiting for runs of this specific deployment.
    execute_water_workflow.serve(
        name=f"{args.node_id}_deployment",
        tags=["water-node", args.node_id]
    )

if __name__ == "__main__":
    main()
