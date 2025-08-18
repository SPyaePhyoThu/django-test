def setup_post_ls_open_instance_public_ports(open_instance_public_ports):

    def post_ls_open_instance_public_ports(from_port, to_port, protocol,cidrs, instance_name):
        return open_instance_public_ports(
            portInfo={
                    'fromPort': from_port,
                    'toPort': to_port,
                    'protocol': protocol,
                    'cidrs': cidrs
                },
            instanceName=instance_name
        )
    return post_ls_open_instance_public_ports