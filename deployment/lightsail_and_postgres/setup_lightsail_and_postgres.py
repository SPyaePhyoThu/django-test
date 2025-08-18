import boto3
import sys
import time
import paramiko
import os

from decouple import config

# Add the project root to sys.path to allow for absolute imports
# The script is at deployment/lightsail_and_postgres/setup_lightsail_and_postgres.py
# The project root is 3 levels up.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from deployment.lightsail_and_postgres.app.action.post_ls_create_instances import setup_post_ls_create_instances as action_post_ls_create_instances
from deployment.lib.app.action.get_ls_instances import setup_get_ls_instance as action_get_ls_instance
from deployment.lib.app.compute.public_ip import public_ip as compute_public_ip
# from deployment.lightsail_and_postgres.app.action.get_ls_instances import setup_get_ls_instance as action_get_ls_instance
# from deployment.lightsail_and_postgres.app.compute.public_ip import public_ip as compute_public_ip
from deployment.lightsail_and_postgres.app.action.post_ls_allocate_static_ip import setup_post_allocate_static_ip as action_post_allocate_static_ip
from deployment.lightsail_and_postgres.app.action.post_ls_attach_static_ip import setup_post_attach_static_ip as action_post_attach_static_ip
from deployment.lightsail_and_postgres.app.action.post_ls_open_instance_public_ports import setup_post_ls_open_instance_public_ports as action_post_ls_open_instance_public_ports
from deployment.lightsail_and_postgres.app.compute.opening_port import opening_port as compute_opening_port
from deployment.lib.app.action.post_ssh_connect import setup_post_ssh_connect as action_post_ssh_connect
# from deployment.lightsail_and_postgres.app.action.post_ssh_connect import setup_post_ssh_connect as action_post_ssh_connect
# from deployment.lightsail_and_postgres.app.compute.ssh_client import ssh_client as compute_ssh_client
from deployment.lib.app.compute.ssh_client import ssh_client as compute_ssh_client
# from deployment.lightsail_and_postgres.app.action.post_ssh_execute_command import setup_post_execute_command as action_post_execute_command
# from deployment.lightsail_and_postgres.app.compute.remote_commands import remote_commands as compute_remote_commands
from deployment.lib.app.action.post_ssh_execute_command import setup_post_execute_command as action_post_execute_command
from deployment.lib.app.compute.remote_commands import remote_commands as compute_remote_commands
from deployment.lightsail_and_postgres.app.compute.instance_status import instance_status as compute_instance_status

# --- Configuration is now managed by the .env file in the project root ---

def main():
    # --- Load Configuration from .env ---
    INSTANCE_NAME = config('INSTANCE_NAME')
    BLUEPRINT_ID = config('BLUEPRINT_ID')
    BUNDLE_ID = config('BUNDLE_ID')
    AVAILABILITY_ZONE = config('AVAILABILITY_ZONE')
    SSH_KEY_PATH = config('SSH_KEY_PATH')
    SSH_USERNAME = config('SSH_USERNAME')
    DB_NAME = config('DB_NAME')
    DB_USER = config('DB_USER')
    DB_PASSWORD = config('DB_PASSWORD')
    STATIC_IP_NAME = f"{INSTANCE_NAME}-static-ip"

    lightsail_client = boto3.client('lightsail')
    ssh_client = paramiko.SSHClient()
    public_ip = None

    try:
        # # --- Step 1: Create Lightsail Instance ---
        # print(f"\n--- Step 1/4: Creating Lightsail instance '{INSTANCE_NAME}' ---")
        # action_post_ls_create_instances(create_instances=lightsail_client.create_instances)(
        #     instance_name=INSTANCE_NAME,
        #     availability_zone=AVAILABILITY_ZONE,
        #     blueprint_id=BLUEPRINT_ID,
        #     bundle_id=BUNDLE_ID,
        #     key_pair_name=f"{INSTANCE_NAME}-key"
        # )

        # print("Waiting for instance to enter 'running' state...")
        # compute_instance_status(
        #     max_attempts=10,
        #     delay=10,
        #     get_ls_instance=action_get_ls_instance(get_instance=lightsail_client.get_instance),
        #     instance_name=INSTANCE_NAME,
        #     time=time,
        #     sys=sys
        # )
        
        # max_attempts = 60
        # delay_seconds = 10
        # for i in range(max_attempts):
        #     try:
        #         instance_info = lightsail_client.get_instance(instanceName=INSTANCE_NAME)
        #         instance_state = instance_info['instance']['state']['name']
        #         print(f"  Attempt {i+1}/{max_attempts}: Current instance state is '{instance_state}'")

        #         if instance_state == 'running':
        #             print("✅ Instance is now running.")
        #             break
        #         elif instance_state in ['pending', 'none']:
        #             time.sleep(delay_seconds)
        #         else:
        #             print(f"❌ Error: Instance entered an unexpected state: '{instance_state}'", file=sys.stderr)
        #             sys.exit(1)
        #     except Exception as e:
        #         print(f"❌ Error while getting instance state: {e}", file=sys.stderr)
        #         time.sleep(delay_seconds)
        # else: # This 'else' belongs to the 'for' loop, it runs if the loop completes without a 'break'
        #     print(f"❌ Error: Instance did not enter 'running' state after {max_attempts * delay_seconds} seconds.", file=sys.stderr)
        #     sys.exit(1)


        # # --- Step 2: Allocate and Attach Static IP ---
        # print(f"\n--- Step 2/5: Allocating and Attaching Static IP---")
        # action_post_allocate_static_ip(allocate_static_ip=lightsail_client.allocate_static_ip)(
        #     name=STATIC_IP_NAME
        # )

        # action_post_attach_static_ip(attach_static_ip=lightsail_client.attach_static_ip)(
        #     ip_name=STATIC_IP_NAME,
        #     instance_name=INSTANCE_NAME
        # )

        # print("⏳ Waiting for attaching static ip...")
        # time.sleep(10)

        public_ip = compute_public_ip(
            get_instance=action_get_ls_instance(get_instance=lightsail_client.get_instance),
            name=INSTANCE_NAME
        )
        print(f"Instance Public IP: {public_ip}")

        # # --- Step 3: Configure Lightsail Firewall ---
        # print(f"\n--- Step 3/5: Configuring Lightsail Firewall for '{INSTANCE_NAME}' ---")
        
        # PORTS_TO_OPEN = [
        #     {"protocol": "tcp", "fromPort": 22, "toPort": 22, "cidrs": ["0.0.0.0/0"]},
        #     {"protocol": "tcp", "fromPort": 80, "toPort": 80, "cidrs": ["0.0.0.0/0"]},
        #     {"protocol": "tcp", "fromPort": 443, "toPort": 443, "cidrs": ["0.0.0.0/0"]},
        #     {"protocol": "tcp", "fromPort": 5432, "toPort": 5432, "cidrs": ["0.0.0.0/0"]},
        # ]
        
        # compute_opening_port(
        #     open_instance_public_ports=action_post_ls_open_instance_public_ports(lightsail_client.open_instance_public_ports),
        #     ports=PORTS_TO_OPEN,
        #     instance_name=INSTANCE_NAME
        # )


        # print("⏳ Waiting for SSH service to initialize after firewall configuration...")
        # time.sleep(60)  # Wait 90 seconds for SSH service to be ready

        # --- Step 4: SSH into instance and run initial setup commands ---
        print(f"\n--- Step 4/5: SSHing into instance {public_ip} and running initial setup ---")
        if not os.path.exists(SSH_KEY_PATH):
            print(f"❌ Error: SSH key not found at {SSH_KEY_PATH}. Please update SSH_KEY_PATH in the script.", file=sys.stderr)
            sys.exit(1)

        ssh_client.load_system_host_keys()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        private_key = paramiko.RSAKey.from_private_key_file(SSH_KEY_PATH)

        compute_ssh_client(
            ssh_connect=action_post_ssh_connect(ssh_client.connect),
            max_retries=15,
            time=time,
            public_ip=public_ip,
            user_name=SSH_USERNAME,
            timeout=30,
            delay=20,
            allow_agent=False,
            look_for_keys= False,
            private_key=private_key
        )

        REMOTE_SETUP_COMMANDS = [
            "sudo apt update && sudo apt upgrade -y",
            "sudo apt install -y git python3-pip python3-venv nginx postgresql postgresql-contrib",
            "sudo systemctl enable postgresql",
            "sudo systemctl start postgresql",
            f"sudo -u postgres psql -c \"CREATE DATABASE {DB_NAME};\"",
            f"sudo -u postgres psql -c \"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}';\"",
            f"sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};\"",
        ]

        compute_remote_commands(
            execute_command=action_post_execute_command(ssh_client.exec_command),
            commands=REMOTE_SETUP_COMMANDS,
            sys=sys
        )

    except lightsail_client.exceptions.ServiceException as e:
        print(f"❌ AWS Service Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if public_ip:
            print(f"\n✅ Server Setup Complete! Your Lightsail instance '{INSTANCE_NAME}' is at IP: {public_ip}")
            print(f"You can SSH into it using: ssh -i {SSH_KEY_PATH} {SSH_USERNAME}@{public_ip}")

        print("\n--- NEXT STEPS ---")
        print(f"1. SSH into your instance: ssh -i {SSH_KEY_PATH} {SSH_USERNAME}@{public_ip}")
        print(f"2. Deploy your Django application code using the 'deploy_django_code.py' script.")
        print("3. Manually configure your Django settings.py file on the server.")
        print("4. Set up Gunicorn, Nginx, and SSL using the respective scripts.")

        if ssh_client:
            ssh_client.close()

if __name__ == "__main__":
    main()
