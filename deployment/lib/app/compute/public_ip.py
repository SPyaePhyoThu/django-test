def public_ip(get_instance, name):

    instance = get_instance(name)
    
    return instance['instance']['publicIpAddress']