def opening_port(open_instance_public_ports, ports, instance_name):
    
    for port in ports:
        protocol = port["protocol"]
        from_port = port["fromPort"]
        to_port = port["toPort"]
        cidrs = port["cidrs"]

        print(f"  Opening port {from_port}-{to_port} ({protocol})...")
        open_instance_public_ports(
            from_port = from_port,
            to_port = to_port,
            protocol = protocol,
            cidrs = cidrs,
            instance_name=instance_name
        )
        print(f"  Port {from_port}-{to_port} opened.")
    print("  Firewall configuration complete.")
