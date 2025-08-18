def ssh_client(ssh_connect, max_retries, time,delay, public_ip,user_name,timeout, allow_agent, look_for_keys, private_key):

    print('hello')
    

    for i in range(max_retries):
        try:
            print(f"  Attempting SSH connection (attempt {i+1}/{max_retries})...")
            ssh_connect(
                host_name=public_ip, 
                user_name=user_name, 
                private_key=private_key, 
                timeout=timeout,
                allow_agent=allow_agent,
                look_for_keys=look_for_keys,
            )
            print("  SSH connection established.")
            return 
        except Exception as e:
            print(f"  SSH connection failed: {e}. Retrying in 10 seconds...")
            time.sleep(delay)
    raise Exception(f"Failed to establish SSH connection to {public_ip} after {max_retries} retries.")    



