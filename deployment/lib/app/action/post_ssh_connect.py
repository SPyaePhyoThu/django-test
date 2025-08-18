def setup_post_ssh_connect(ssh_connect):

    def post_ssh_connect(host_name, user_name, private_key, timeout, allow_agent, look_for_keys):
        return ssh_connect(
            hostname=host_name,
            username=user_name,
            pkey=private_key,
            timeout=timeout,
            allow_agent=allow_agent,
            look_for_keys=look_for_keys,
        )
    
    return post_ssh_connect