def remote_commands(execute_command, commands, sys):

    for command in commands:
        print(f"Executing {command}")
        stdin, stdout, stderr = execute_command(command)
        stdout_output = stdout.read().decode().strip()
        stderr_output = stderr.read().decode().strip()

        if stdout_output:
            print(f"  STDOUT: {stdout_output}")
        if stderr_output:
            print(f"  STDERR: {stderr_output}")

        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            print(f"❌ Command failed with exit status {exit_status}: {command}", file=sys.stderr)
            sys.exit(1)
