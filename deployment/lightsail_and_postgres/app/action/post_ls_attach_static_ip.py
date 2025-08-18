def setup_post_attach_static_ip(attach_static_ip):

    def post_attach_static_ip(ip_name, instance_name):
        return attach_static_ip(
            staticIpName=ip_name,
            instanceName=instance_name
        )
    
    return post_attach_static_ip