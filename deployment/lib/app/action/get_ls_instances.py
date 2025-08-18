def setup_get_ls_instance(get_instance):
    
    def get_ls_instance(name):
        return get_instance(
            instanceName=name
        )
    
    return get_ls_instance