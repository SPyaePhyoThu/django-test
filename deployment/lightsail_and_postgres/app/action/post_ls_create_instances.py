def setup_post_ls_create_instances(create_instances):

    def post_ls_create_instances(instance_name,availability_zone,blueprint_id,bundle_id, key_pair_name):
        return create_instances(
                instanceNames=[
                    instance_name,
                ],
                availabilityZone=availability_zone,
                blueprintId=blueprint_id,
                bundleId=bundle_id,
                keyPairName=key_pair_name
            )
    return post_ls_create_instances
