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
    Restores a PostgreSQL database on a Lightsail instance from a local backup file.
    This is a destructive operation and will wipe the existing database.
    """
    # --- Load Configuration from .env ---
    INSTANCE_NAME = config('INSTANCE_NAME')
    SSH_KEY_PATH = config('SSH_KEY_PATH')
    SSH_USERNAME = config('SSH_USERNAME')
    DB_NAME = config('DB_NAME')
    DB_USER = config('DB_USER')
    LOCAL_BACKUP_DIR = config('LOCAL_BACKUP_DIR', default='./backups')
    S3_REGION = config('AWS_REGION', default=None)

    # --- Step 1: Select a backup file ---
    print(f"--- Searching for backup files in '{LOCAL_BACKUP_DIR}' ---")
    if not os.path.isdir(LOCAL_BACKUP_DIR):
        print(f"❌ Error: Local backup directory not found at '{LOCAL_BACKUP_DIR}'", file=sys.stderr)
        sys.exit(1)

    backup_files = sorted([f for f in os.listdir(LOCAL_BACKUP_DIR) if f.endswith('.sql')], reverse=True)
    if not backup_files:
        print(f"❌ No .sql backup files found in '{LOCAL_BACKUP_DIR}'", file=sys.stderr)
        sys.exit(1)

    print("Available backup files (newest first):")
    for i, filename in enumerate(backup_files):
        print(f"  {i + 1}: {filename}")

    try:
        choice = int(input("Enter the number of the backup file to restore: ")) - 1
        if not 0 <= choice < len(backup_files):
            raise ValueError()
        chosen_backup_file = backup_files[choice]
        local_backup_path = os.path.join(LOCAL_BACKUP_DIR, chosen_backup_file)
    except (ValueError, IndexError):
        print("❌ Invalid selection.", file=sys.stderr)
        sys.exit(1)

    print(f"\nSelected backup: {chosen_backup_file}")

    # --- Step 2: Critical Warning and Confirmation ---
    print("\n" + "="*60)
    print("🚨 CRITICAL WARNING 🚨")
    print("="*60)
    print(f"You are about to WIPE the existing database '{DB_NAME}'")
    print(f"on the instance '{INSTANCE_NAME}' and replace it with the contents")
    print(f"of '{chosen_backup_file}'.")
    print("\nTHIS ACTION IS IRREVERSIBLE.")
    print("="*60)

    confirmation = input(f"To confirm, please type the instance name ('{INSTANCE_NAME}'): ")
    if confirmation != INSTANCE_NAME:
        print("\n❌ Confirmation failed. Aborting restore operation.")
        sys.exit(0)

    print("\n✅ Confirmation received. Proceeding with database restore...")

    ssh_client = None
    try:
        # --- Step 3: Connect to Instance and Upload Backup ---
        lightsail_client = boto3.client('lightsail', region_name=S3_REGION)
        public_ip = compute_public_ip(
            get_instance=action_get_ls_instance(get_instance=lightsail_client.get_instance),
            name=INSTANCE_NAME
        )
        
        print(f"\n--- Connecting to instance {public_ip} via SSH ---")
        ssh_client = paramiko.SSHClient()
        ssh_client.load_system_host_keys()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        compute_ssh_client(
            ssh_connect=action_post_ssh_connect(ssh_client.connect),
            max_retries=5, time=time, public_ip=public_ip, user_name=SSH_USERNAME,
            ssh_key_path=SSH_KEY_PATH, timeout=10, delay=10
        )

        remote_temp_path = f"/tmp/{chosen_backup_file}"
        print(f"--- Uploading '{chosen_backup_file}' to remote server at '{remote_temp_path}' ---")
        sftp = ssh_client.open_sftp()
        sftp.put(local_backup_path, remote_temp_path)
        sftp.close()
        print("✅ Upload complete.")

        # --- Step 4: Execute Restore Commands ---
        print(f"--- Resetting and restoring database '{DB_NAME}' ---")
        # This command terminates any active connections to the target database,
        # which is necessary before it can be dropped.
        restore_commands = [
            f"sudo -u postgres psql -c 'SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = \'{DB_NAME}\';'",
            f"sudo -u postgres psql -c 'DROP DATABASE IF EXISTS {DB_NAME};'",
            f"sudo -u postgres psql -c 'CREATE DATABASE {DB_NAME};'",
            f"sudo -u postgres psql -c 'GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};'",
            f"sudo -u postgres psql -d {DB_NAME} -f {remote_temp_path}"
        ]

        compute_remote_commands(
            execute_command=action_post_execute_command(ssh_client.exec_command),
            commands=restore_commands,
            sys=sys
        )
        print("✅ Database restored successfully.")

        # --- Step 5: Cleanup ---
        print(f"--- Cleaning up remote backup file '{remote_temp_path}' ---")
        compute_remote_commands(
            execute_command=action_post_execute_command(ssh_client.exec_command),
            commands=[f"rm {remote_temp_path}"],
            sys=sys
        )
        print("✅ Cleanup complete.")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred during the restore process: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if ssh_client:
            ssh_client.close()
        print("\n--- Restore script finished. ---")


if __name__ == "__main__":
    main()
