def setup_post_execute_command(execute_command):

    def post_execute_command(command):

        return execute_command(
            command
        )
    return post_execute_command
