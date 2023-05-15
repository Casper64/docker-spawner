from flask import Flask, request
import subprocess
import random
import re

# Docker container port range
PORT_START = 9000
# Maximum number of containers
MAX_CONTAINERS = 3

# The name of the proxy configuration file
PROXY_CONFIG = 'dynamic_proxy.conf'
# Name of your domain
DOMAIN = 'example.com'
# Length of the hex identifier
HEX_SIZE = 32
# Prefix for spawned docker containers
CONTAINER_PREFIX = 'spawned__'

# Add your container images here
CONTAINER_IMAGES: dict[str, str] = {
    # 'some_id': 'container_name'
}


app = Flask(__name__)

# Mapping of hex IDs to container information
container_map = {}


@app.route('/spawn', methods=['POST'])
def create_container():
    """'/spawn' takes the parameter `container_id` and starts the docker container for that id.
    returns the hex identifier of that container when the container is running.
    the container can then be accessed at `http://[return_value].[DOMAIN]`"""

    # Validate request parameters
    container_id = request.form['container_id']
    if container_id == '':
        return "Bad request: no 'container_id' is required", 400

    if container_id not in CONTAINER_IMAGES:
        return f"Error: docker image for id '{container_id} does not exist!", 400

    if (port := get_available_port()) == -1:
        return f"Error: max available containers reached!", 409

    docker_image = CONTAINER_IMAGES[container_id]

    print(f"Starting container for docker image {docker_image} on port {port}")

    # Start container
    try:
        output = subprocess.check_call(
            f"docker run -d -p {port}:80 --name {CONTAINER_PREFIX}{docker_image}__{port} {docker_image}", shell=True)
        if output != 0:
            return "Error starting docker", 500
    except subprocess.CalledProcessError:
        return "Error starting docker", 500

    # Set custom hash as id. The docker digest hash is 64 characters, a bit long
    container_digest = gen_random_hex_string(HEX_SIZE)
    container_map[container_digest] = port

    update_proxy_config()

    return container_digest


def get_available_port() -> int:
    """Get an available port in the port range. Returns -1 if all ports are used."""
    used_ports = set(container_map.values())
    all_ports = set(range(PORT_START, PORT_START+MAX_CONTAINERS))
    available_ports = all_ports.difference(used_ports)

    if len(available_ports) == 0:
        return -1
    else:
        return available_ports.pop()


def update_proxy_config():
    """see function name"""

    # save the old configuration
    with open(PROXY_CONFIG, 'r') as f:
        old_config = f.read()

    rewrite_rules: list[str] = []

    for hex, port in container_map.items():
        rule = f"""RewriteCond %{{HTTP_HOST}} ={hex}.{DOMAIN}
RewriteRule ^/(.*) http://localhost:{port}/$1 [P,L]
ProxyPassReverse / http://localhost:{port}/"""
        rewrite_rules.append(rule)

    rewrite_rules_str = '\n\n'.join(rewrite_rules)
    new_file = f"""RewriteEngine On

{rewrite_rules_str}    

RewriteRule ^ - [L,R=404]"""

    with open(PROXY_CONFIG, 'w') as f:
        f.write(new_file)

    # Reload apache
    try:
        subprocess.check_call('sudo systemctl reload apache2', shell=True)
    except subprocess.CalledProcessError:
        print('Reloading apache failed!')
        with open(PROXY_CONFIG, 'w') as f:
            f.write(old_config)

        # old_config should not fail
        subprocess.check_call('sudo systemctl reload apache2')


def gen_random_hex_string(size):
    return ''.join(random.choices('0123456789abcdef', k=size))


def get_all_running_containers():
    """Run at startup to load all running contains that were spawned by the service into 
    `container_map`. Hex ids will be changed so call `update_proxy_config` next."""
    try:
        output = subprocess.check_output(
            f'sudo docker ps -f "name={CONTAINER_PREFIX}"')
    except subprocess.CalledProcessError:
        return

    containers = output.splitlines()
    if len(containers) == 1:
        return

    containers = containers[1:]

    for docker_str in containers:
        obj = re.search("spawned__(.+)__(\d+)", docker_str.decode())
        _, port = obj.groups()
        port = int(port)

        hex = gen_random_hex_string(HEX_SIZE)
        container_map[hex] = port

    print(container_map)
