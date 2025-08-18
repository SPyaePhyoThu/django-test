import paramiko
import sys
import os
import time
import boto3
from decouple import config
from datetime import datetime

from ..lib.app.action.get_ls_instances import setup_get_ls_instance as action_get_ls_instance
from ..lib.app.compute.public_ip import public_ip as compute_public_ip
from ..lib.app.action.post_ssh_connect import setup_post_ssh_connect as action_post_ssh_connect
from ..lib.app.compute.ssh_client import ssh_client as compute_ssh_client
from ..lib.app.action.post_ssh_execute_command import setup_post_execute_command as action_post_execute_command
from ..lib.app.compute.remote_commands import remote_commands as compute_remote_commands

def main():    
    # --- Load Configuration from .env ---   #
    INSTANCE_NAME = config('INSTANCE_NAME')    
    SSH_KEY_PATH = config('SSH_KEY_PATH')    
    SSH_USERNAME = config('SSH_USERNAME')    
    DB_NAME = config('DB_NAME')    
    REMOTE_BACKUP_DIR = config('REMOTE_BACKUP_DIR', default='/home/ubuntu/backups')    
    LOCAL_BACKUP_DIR = config('LOCAL_BACKUP_DIR', default='./backups')    
    S3_BUCKET_NAME = config('S3_BUCKET_NAME', default=None)    
    S3_REGION = config('AWS_REGION', default=None)   


    if not S3_BUCKET_NAME:        
        print("❌ Error: S3_BUCKET_NAME is not configured in your .env file.", file=sys.stderr)        
        print("Please add it to enable S3 uploads.", file=sys.stderr)        
        sys.exit(1)    
        ssh_client = None    
        try:        
            lightsail_client = boto3.client('lightsail', region_name=S3_REGION)        
            # --- Get Public IP and Connect via SSH ---        
            public_ip = compute_public_ip( 
                get_instance=action_get_ls_instance(get_instance=lightsail_client.get_instance),            
                name=INSTANCE_NAME        
            )        
            print(f"Instance Public IP: {public_ip}")        
            if not os.path.exists(SSH_KEY_PATH):            
                print(f"❌ Error: SSH key not found at {SSH_KEY_PATH}.", file=sys.stderr)            
                sys.exit(1)        
                
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
                    delay=10        
                )
                


                # --- Create remote backup directory ---        
                
                print(f"\n--- Ensuring remote backup directory exists: {REMOTE_BACKUP_DIR} ---")        
                compute_remote_commands(            
                    execute_command=action_post_execute_command(ssh_client.exec_command),            
                    commands=[f"mkdir -p {REMOTE_BACKUP_DIR}"],            
                    sys=sys        
                )        
                # --- Perform Backup ---        
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")        
                
                backup_file_name = f"{DB_NAME}_backup_{timestamp}.sql"        
                remote_backup_path = f"{REMOTE_BACKUP_DIR}/{backup_file_name}"        
                
                print(f"\n--- Backing up database '{DB_NAME}' to '{remote_backup_path}' ---")        
                backup_command = f"sudo -u postgres pg_dump {DB_NAME} > {remote_backup_path}"        
                compute_remote_commands(            
                    execute_command=action_post_execute_command(ssh_client.exec_command),            
                    commands=[backup_command],            
                    sys=sys        
                )        
                print("✅ Remote backup created successfully.")        
                # --- Download backup file ---        
                if not os.path.exists(LOCAL_BACKUP_DIR):            
                    os.makedirs(LOCAL_BACKUP_DIR)                
                    local_backup_path = os.path.join(LOCAL_BACKUP_DIR, backup_file_name)        
                    print(f"\n--- Downloading backup file to '{local_backup_path}' ---")        
                    sftp = ssh_client.open_sftp()        
                    sftp.get(remote_backup_path, local_backup_path)        
                    sftp.close()        
                    print("✅ Backup file downloaded successfully.")   
                    
                    # --- Upload backup to S3 ---        
                    print(f"\n--- Uploading backup to S3 bucket '{S3_BUCKET_NAME}' ---")  

                    s3_client = boto3.client('s3', region_name=S3_REGION)        
                    s3_key = f"database-backups/{backup_file_name}"        
                    s3_client.upload_file(local_backup_path, S3_BUCKET_NAME, s3_key)   
                    
                    print(f"✅ Backup uploaded to S3 successfully as '{s3_key}'.")    
        except Exception as e:        
            print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)        
            sys.exit(1)    
        finally:        
            if ssh_client:            
                ssh_client.close()

if __name__ == "__main__":
    main()
