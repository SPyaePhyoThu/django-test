
"""
Creates and saves a Lightsail SSH key pair.

This script is intended to be run before the main instance setup script.
It creates a new SSH key pair in AWS Lightsail, saves the private key
to a .pem file, and sets the correct permissions.

It reads the INSTANCE_NAME from the .env file in the project root.
The generated key will be named based on the instance name.
"""
import boto3
import os
import sys
import base64
from decouple import config, UndefinedValueError

def main():
    """
    Main function to create and save the Lightsail SSH key pair.
    """
    try:
        instance_name = config('INSTANCE_NAME')
        availability_zone = config('AVAILABILITY_ZONE')
        region = availability_zone[:-1]  # e.g., us-east-1a -> us-east-1
    except UndefinedValueError as e:
        print(f"❌ Error: Missing configuration in .env file: {e}", file=sys.stderr)
        print("Please ensure INSTANCE_NAME and AVAILABILITY_ZONE are set in your .env file.", file=sys.stderr)
        sys.exit(1)

    key_pair_name = f"{instance_name}-key"
    
    # Save the key in the project root directory, which is three levels up from this script.
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ssh_key_filepath = os.path.join(project_root, f"{key_pair_name}.pem")

    lightsail_client = boto3.client('lightsail', region_name=region)

    print(f"--- Setting up SSH key pair: {key_pair_name} ---")

    try:
        # Check if key pair already exists on Lightsail
        lightsail_client.get_key_pair(keyPairName=key_pair_name)
        print(f"Key pair '{key_pair_name}' already exists on Lightsail.")
        if not os.path.exists(ssh_key_filepath):
            print(f"❌ Error: Key pair '{key_pair_name}' exists on AWS but the local file '{ssh_key_filepath}' is missing.", file=sys.stderr)
            print(f"Please delete the key pair from the Lightsail console or locate the file and place it in the project root, then re-run.", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"Using existing local key file: {ssh_key_filepath}")

    except lightsail_client.exceptions.NotFoundException:
        # Key pair does not exist, so create it
        print(f"Creating new key pair '{key_pair_name}' on Lightsail.")
        try:
            key_pair_response = lightsail_client.create_key_pair(keyPairName=key_pair_name)
            
            # The 'privateKeyBase64' field from the Lightsail API appears to contain the raw PEM content
            # directly, contrary to its name. The base64 decoding step is removed.
            private_key_pem = key_pair_response['privateKeyBase64']

            with open(ssh_key_filepath, "w") as key_file:
                key_file.write(private_key_pem)

            # Set permissions to 400 (read-only for owner)
            os.chmod(ssh_key_filepath, 0o400)

            print(f"✅ Private key saved to '{ssh_key_filepath}'. PROTECT THIS FILE!")
            print("\n--- NEXT STEPS ---")
            print(f"1. Your new SSH key path is: {ssh_key_filepath}")
            print(f"2. Update your .env file with: SSH_KEY_PATH='{ssh_key_filepath}'")

        except Exception as e:
            print(f"❌ Error creating key pair: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
