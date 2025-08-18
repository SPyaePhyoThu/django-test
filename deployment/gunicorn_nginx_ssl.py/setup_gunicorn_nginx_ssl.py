import paramiko
import sys
import os
import time
import boto3
from decouple import config

from ..lib.app.action.get_ls_instances import setup_get_ls_instance as action_get_ls_instance
from ..lib.app.compute.public_ip import public_ip as compute_public_ip
from ..lib.app.action.post_ssh_connect import setup_post_ssh_connect as action_post_ssh_connect
from ..lib.app.compute.ssh_client import ssh_client as compute_ssh_client
from ..lib.app.action.post_ssh_execute_command import setup_post_execute_command as action_post_execute_command
from ..lib.app.compute.remote_commands import remote_commands as compute_remote_commands

# --- Configuration is now managed by the .env file in the project root ---

def main():
    # --- Load Configuration from .env ---
    INSTANCE_NAME = config('INSTANCE_NAME')
    SSH_KEY_PATH = config('SSH_KEY_PATH')
    SSH_USERNAME = config('SSH_USERNAME')
    REMOTE_PROJECT_DIR = config('REMOTE_PROJECT_DIR')
    DJANGO_PROJECT_NAME = config('DJANGO_PROJECT_NAME')
    DOMAIN_NAME = config('DOMAIN_NAME')
    CERTBOT_EMAIL = config('CERTBOT_EMAIL')

    lightsail_client = boto3.client('lightsail')
    ssh_client = None

    try:
        # --- SSH Connection ---
        public_ip = compute_public_ip(
            get_instance=action_get_ls_instance(get_instance=lightsail_client.get_instance),
            name=INSTANCE_NAME
        )
        if not os.path.exists(SSH_KEY_PATH):
            print(f"❌ Error: SSH key not found at {SSH_KEY_PATH}. Please update SSH_KEY_PATH in the script.", file=sys.stderr)
            sys.exit(1)

        if not DOMAIN_NAME or DOMAIN_NAME == "your_domain.com":
            print("❌ Error: DOMAIN_NAME is not set or is still the placeholder. This is required.", file=sys.stderr)
            sys.exit(1)
        
        print(f"\n--- Connecting to {public_ip} via SSH for Server Configuration ---")
        ssh_client = paramiko.SSHClient()
        ssh_client.load_system_host_keys()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        compute_ssh_client(
            ssh_connect=action_post_ssh_connect(ssh_client.connect),
            max_retries=5,
            time=time,
            public_ip=public_ip,
            user_name=SSH_USERNAME,
            ssh_key_path=SSH_KEY_PATH,
            timeout=10,
            delay=5
        )

        # === PART 1: GUNICORN SETUP ===
        print("\n--- PART 1: Creating Gunicorn Systemd Service File ---")
        gunicorn_service_content = f"""
        [Unit]
        Description=gunicorn daemon
        After=network.target

        [Service]
        User={SSH_USERNAME}
        Group={SSH_USERNAME}
        WorkingDirectory={REMOTE_PROJECT_DIR}
        ExecStart={REMOTE_PROJECT_DIR}/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:{REMOTE_PROJECT_DIR}/{DJANGO_PROJECT_NAME}.sock {DJANGO_PROJECT_NAME}.wsgi:application
        Restart=on-failure

        [Install]
        WantedBy=multi-user.target
        """
        gunicorn_service_content_escaped = gunicorn_service_content.replace("'", "'''")
        command_gunicorn = f"echo -e '''{gunicorn_service_content_escaped}'''' | sudo tee /etc/systemd/system/gunicorn.service"
        compute_remote_commands(
            execute_command=action_post_execute_command(ssh_client.exec_command),
            commands=[command_gunicorn],
            sys=sys
        )

        systemctl_commands = [
            "sudo systemctl daemon-reload",
            "sudo systemctl start gunicorn",
            "sudo systemctl enable gunicorn"
        ]

        print("\n--- Starting and Enabling Gunicorn Service ---")
        compute_remote_commands(
            execute_command=action_post_execute_command(ssh_client.exec_command),
            commands=systemctl_commands,
            sys=sys
        )
        print("✅ Gunicorn setup complete.")

        # === PART 2: NGINX SETUP ===
        print("\n--- PART 2: Creating Nginx Configuration File ---")
        server_name = f"{DOMAIN_NAME} www.{DOMAIN_NAME}"
        nginx_config_content = f"""
        server {{
            listen 80;
            server_name {server_name};

            location = /favicon.ico {{ access_log off; log_not_found off; }}
            location /static/ {{
                root {REMOTE_PROJECT_DIR};
            }}

            location / {{
                include proxy_params;
                proxy_pass http://unix:{REMOTE_PROJECT_DIR}/{DJANGO_PROJECT_NAME}.sock;
            }}
        }}
        """
        nginx_config_content_escaped = nginx_config_content.replace("'", "'''")
        config_file_path = f"/etc/nginx/sites-available/{DJANGO_PROJECT_NAME}.conf"
        command_nginx = f"echo -e '''{nginx_config_content_escaped}'''' | sudo tee {config_file_path}"

        compute_remote_commands(
            execute_command=action_post_execute_command(ssh_client.exec_command),
            commands=[command_nginx],
            sys=sys
        )

        print("\n--- Enabling Nginx Configuration and Restarting Nginx ---")
        compute_remote_commands(
            execute_command=action_post_execute_command(ssh_client.exec_command),
            commands=["sudo rm -f /etc/nginx/sites-enabled/default"],
            sys=sys
        )

        symlink_path = f"/etc/nginx/sites-enabled/{DJANGO_PROJECT_NAME}.conf"
        nginx_setup_commands = [
            f"sudo ln -sf {config_file_path} {symlink_path}",
            "sudo nginx -t",
            "sudo systemctl restart nginx"
        ]

        compute_remote_commands(
            execute_command=action_post_execute_command(ssh_client.exec_command),
            commands=nginx_setup_commands,
            sys=sys
        )
        print("✅ Nginx setup complete.")

        # === PART 3: SSL/HTTPS SETUP ===
        print("\n--- PART 3: Installing Certbot and Obtaining SSL Certificate ---")

        ssl_https_setup_commands = [
            "sudo snap install core; sudo snap refresh core",
            "sudo snap install --classic certbot"
        ]
        compute_remote_commands(
            execute_command=action_post_execute_command(ssh_client.exec_command),
            commands=ssl_https_setup_commands,
            sys=sys
        )

        compute_remote_commands(
            execute_command=action_post_execute_command(ssh_client.exec_command),
            commands=["sudo ln -s /snap/bin/certbot /usr/bin/certbot"],
            sys=sys
        )

        certbot_command = f"sudo certbot --nginx -d {DOMAIN_NAME} -d www.{DOMAIN_NAME} --non-interactive --agree-tos --email {CERTBOT_EMAIL} --redirect"
        compute_remote_commands(
            execute_command=action_post_execute_command(ssh_client.exec_command),
            commands=[certbot_command],
            sys=sys
        )

        print("\n✅ SSL setup complete. Your site should now be accessible via HTTPS.")
        print(f"Try accessing your application at https://{DOMAIN_NAME}/")

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
