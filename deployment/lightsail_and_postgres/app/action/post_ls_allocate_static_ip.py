def setup_post_allocate_static_ip(allocate_static_ip):

    def post_allocate_static_ip(name):
        return allocate_static_ip(
            staticIpName=name
        )
    
    return post_allocate_static_ip