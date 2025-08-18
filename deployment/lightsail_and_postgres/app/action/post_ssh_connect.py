def setup_post_ssh_connect(ssh_connect):

    def post_ssh_connect(host_name, user_name, private_key, timeout):
        return ssh_connect(
            hostname=host_name,
            username=user_name,
            pkey=private_key,
            timeout=timeout,
            allow_agent=False,
            look_for_keys=False,
        )
    
    return post_ssh_connect