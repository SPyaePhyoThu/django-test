import paramiko
import sys
import os
import time
import boto3
from decouple import config

# Import shared components from the deployment library
from ..lib.app.action.get_ls_instances import setup_get_ls_instance as action_get_ls_instance
from ..lib.app.compute.public_ip import public_ip as compute_public_ip
from ..lib.app.action.post_ssh_connect import setup_post_ssh_connect as action_post_ssh_connect
from ..lib.app.compute.ssh_client import ssh_client as compute_ssh_client
from ..lib.app.action.post_ssh_execute_command import setup_post_execute_command as action_post_execute_command
from ..lib.app.compute.remote_commands import remote_commands as compute_remote_commands


def main():
    """
    Connects to the Lightsail instance and deploys the latest version of the
    'main' branch from the Git repository.
    """
    # --- Load Configuration from .env ---
    INSTANCE_NAME = config('INSTANCE_NAME')
    SSH_KEY_PATH = config('SSH_KEY_PATH')
    SSH_USERNAME = config('SSH_USERNAME')
    REMOTE_PROJECT_DIR = config('REMOTE_PROJECT_DIR')
    DJANGO_PROJECT_NAME = config('DJANGO_PROJECT_NAME')

    print(f"--- Starting application update for instance '{INSTANCE_NAME}' from 'main' branch ---")

    ssh_client = None
    try:
        # --- Connect to the instance ---
        lightsail_client = boto3.client('lightsail')
        public_ip = compute_public_ip(
            get_instance=action_get_ls_instance(get_instance=lightsail_client.get_instance),
            name=INSTANCE_NAME
        )

        print(f"--- Connecting to instance {public_ip} via SSH ---")
        ssh_client = paramiko.SSHClient()
        ssh_client.load_system_host_keys()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        compute_ssh_client(
            ssh_connect=action_post_ssh_connect(ssh_client.connect),
            max_retries=5, time=time, public_ip=public_ip, user_name=SSH_USERNAME,
            ssh_key_path=SSH_KEY_PATH, timeout=10, delay=10
        )

        # --- Define paths and commands for the update ---
        python_path = f"{REMOTE_PROJECT_DIR}/venv/bin/python"
        pip_path = f"{REMOTE_PROJECT_DIR}/venv/bin/pip"
        manage_py_path = f"{REMOTE_PROJECT_DIR}/{DJANGO_PROJECT_NAME}/manage.py"

        # These commands are chained with '&&' to ensure that the script will
        # stop immediately if any single command fails.
        update_commands = [
            f"cd {REMOTE_PROJECT_DIR}",
            "git checkout main",  # Ensure we are on the main branch
            "git pull origin main",
            f"{pip_path} install -r requirements.txt",
            f"{python_path} {manage_py_path} migrate",
            f"{python_path} {manage_py_path} collectstatic --noinput",
            "sudo systemctl restart gunicorn"
        ]

        full_command = " && ".join(update_commands)

        print("--- Running update commands on the server ---")
        compute_remote_commands(
            execute_command=action_post_execute_command(ssh_client.exec_command),
            commands=[full_command],
            sys=sys
        )

        print("\n✅ Application update complete.")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred during the update: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if ssh_client:
            ssh_client.close()


if __name__ == "__main__":
    main()
