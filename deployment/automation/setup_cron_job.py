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
    Connects to a Lightsail instance and sets up a cron job for automated backups.
    The cron job is added idempotently, meaning it won't be duplicated if run again.
    """
    # --- Load Configuration from .env ---
    INSTANCE_NAME = config('INSTANCE_NAME')
    SSH_KEY_PATH = config('SSH_KEY_PATH')
    SSH_USERNAME = config('SSH_USERNAME')
    REMOTE_PROJECT_DIR = config('REMOTE_PROJECT_DIR')
    CRON_SCHEDULE = config('CRON_SCHEDULE', default='5 2 * * *')  # Default: 2:05 AM daily
    S3_REGION = config('AWS_REGION', default=None)

    print("--- Setting up automated backup cron job ---")

    ssh_client = None
    try:
        # --- Connect to the instance ---
        lightsail_client = boto3.client('lightsail', region_name=S3_REGION)
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

        # --- Construct the idempotent cron command ---
        python_path = f"{REMOTE_PROJECT_DIR}/venv/bin/python"
        log_path = f"{REMOTE_PROJECT_DIR}/backup.log"

        # The full command to be executed by cron
        cron_command = f"cd {REMOTE_PROJECT_DIR} && {python_path} -m deployment.backup.backup_postgres_db >> {log_path} 2>&1"
        
        # The final cron job entry, including the schedule
        cron_job_entry = f"{CRON_SCHEDULE} {cron_command}"

        # This shell command safely adds the cron job. It first checks if the exact job
        # already exists. If not, it adds the new job to the existing crontab.
        idempotent_command = """
        CRON_JOB='{cron_job_entry}'
        (crontab -l 2>/dev/null | grep -F -q "$CRON_JOB") || \
        ( (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab - )
        """

        print(f"--- Adding the following cron job to the server ---\n{cron_job_entry}")

        compute_remote_commands(
            execute_command=action_post_execute_command(ssh_client.exec_command),
            commands=[idempotent_command],
            sys=sys
        )

        print("\n✅ Cron job for automated backups set up successfully.")
        print("You can verify by SSHing into the server and running 'crontab -l'.")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if ssh_client:
            ssh_client.close()


if __name__ == "__main__":
    main()
