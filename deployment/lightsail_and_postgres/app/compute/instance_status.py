def instance_status(max_attempts , delay,get_ls_instance, instance_name, time, sys):
    
    instance_running = False

    for i in range(max_attempts):
        try:
            instance_info = get_ls_instance(name=instance_name)
            instance_state = instance_info['instance']['state']['name']
            print(f" Attempt {i+1}/{max_attempts}: Current instance state is '{instance_state}'")

            if instance_state == 'running':
                print("✅ Instance is now running.")
                instance_running = True
                break
            elif instance_state in ['pending', 'none']:
                time.sleep(delay)

        except Exception as e:
            print(f"❌ Error while getting instance state: {e}", file=sys.stderr)
            time.sleep(delay)
    
    # Check after the loop
    if not instance_running:
        print(f"❌ Error: Instance did not enter 'running' state after {max_attempts * delay} seconds.", file=sys.stderr)
        sys.exit(1)