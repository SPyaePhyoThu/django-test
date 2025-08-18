import paramiko
import sys
import os
import time
import boto3
from decouple import config

from deployment.lib.app.action.get_ls_instances import setup_get_ls_instance as action_get_ls_instance
from deployment.lib.app.compute.public_ip import public_ip as compute_public_ip
from deployment.lib.app.action.post_ssh_connect import setup_post_ssh_connect as action_post_ssh_connect
from deployment.lib.app.compute.ssh_client import ssh_client as compute_ssh_client
from deployment.lib.app.action.post_ssh_execute_command import setup_post_execute_command as action_post_execute_command
from deployment.lib.app.compute.remote_commands import remote_commands as compute_remote_commands

# --- Configuration is now managed by the .env file in the project root ---

def main():
    # --- Load Configuration from .env ---
    INSTANCE_NAME = config('INSTANCE_NAME')
    SSH_KEY_PATH = config('SSH_KEY_PATH')
    SSH_USERNAME = config('SSH_USERNAME')
    GITHUB_REPO_URL = config('GITHUB_REPO_URL')
    REMOTE_PROJECT_DIR = config('REMOTE_PROJECT_DIR')
    DJANGO_PROJECT_NAME = config('DJANGO_PROJECT_NAME')

    lightsail_client = boto3.client('lightsail')
    ssh_client = None

    try:
        public_ip = compute_public_ip(
            get_instance=action_get_ls_instance(get_instance=lightsail_client.get_instance),
            name=INSTANCE_NAME
        )
        print(f"Instance Public IP: {public_ip}")

        if not os.path.exists(SSH_KEY_PATH):
            print(f"❌ Error: SSH key not found at {SSH_KEY_PATH}. Please update SSH_KEY_PATH in the script.", file=sys.stderr)
            sys.exit(1)
        
        ssh_client = paramiko.SSHClient()
        ssh_client.load_system_host_keys()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        private_key = paramiko.RSAKey.from_private_key_file(SSH_KEY_PATH)

        compute_ssh_client(
            ssh_connect=action_post_ssh_connect(ssh_client.connect),
            max_retries=5,
            time=time,
            public_ip=public_ip,
            user_name=SSH_USERNAME,
            timeout=10,
            allow_agent=False,
            look_for_keys= False,
            delay=10,
            private_key=private_key
        )

        print(f"\n--- Running Initial Setup Commands ---")
        initial_setup_commands = [
            f"sudo mkdir -p {REMOTE_PROJECT_DIR}",
            f"sudo chown {SSH_USERNAME}:{SSH_USERNAME} {REMOTE_PROJECT_DIR}",
            f"git clone {GITHUB_REPO_URL} {REMOTE_PROJECT_DIR}",
            f"python3 -m venv {REMOTE_PROJECT_DIR}/venv"
        ]

        compute_remote_commands(
            execute_command=action_post_execute_command(ssh_client.exec_command),
            commands=initial_setup_commands,
            sys=sys
        )

        PYTHON_EXEC = f"{REMOTE_PROJECT_DIR}/venv/bin/python3"
        PIP_EXEC = f"{REMOTE_PROJECT_DIR}/venv/bin/pip"

        print("\n--- Running Django-specific Commands ---")
        django_commands = [
            f"{PIP_EXEC} install -r {REMOTE_PROJECT_DIR}/requirements.txt",
            f"{PYTHON_EXEC} {REMOTE_PROJECT_DIR}/{DJANGO_PROJECT_NAME}/manage.py migrate",
            f"{PYTHON_EXEC} {REMOTE_PROJECT_DIR}/{DJANGO_PROJECT_NAME}/manage.py collectstatic --noinput"
        ]

        compute_remote_commands(
            execute_command=action_post_execute_command(ssh_client.exec_command),
            commands=django_commands,
            sys=sys
        )

    except paramiko.AuthenticationException:
        print(f"❌ Authentication failed. Check your SSH key and permissions for {SSH_KEY_PATH}", file=sys.stderr)
        sys.exit(1)
    except paramiko.SSHException as e:
        print(f"❌ SSH connection error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if ssh_client:
            ssh_client.close()

if __name__ == "__main__":
    main()
