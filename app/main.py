from flask import request, Blueprint
import subprocess
import random
import re
from . import settings
from os.path import exists


# Mapping of hex IDs to container information
container_map = {}

# Flask routes
bp = Blueprint('main', __name__)


#           ROUTES
# ============================

@bp.route('/spawn', methods=['POST'])
def create_container():
    """'/spawn' takes the parameter `container_id` and starts the docker container for that id.
    returns the hex identifier of that container when the container is running.
    the container can then be accessed at `http://[return_value].[DOMAIN]`"""

    print('got request', request.form)

    # Validate request parameters
    container_id = request.form['container_id']
    if container_id == '':
        return "Bad request: field 'container_id' is required", 400

    if container_id not in settings.CONTAINER_IMAGES:
        return f"Error: docker image for id '{container_id} does not exist!", 400

    if settings.WITH_USERS:
        user_id = request.form['user_id']
        if user_id == '':
            return "Bad request: field 'user_id' is required", 400

    if (port := get_available_port()) == -1:
        return f"Error: max available containers reached!", 409

    docker_image = settings.CONTAINER_IMAGES[container_id]

    print(f"Starting container for docker image {docker_image} on port {port}")

    prefix = ""
    if not settings.WINDOWS:
        prefix = "sudo "

    container_name = f"{settings.CONTAINER_PREFIX}{docker_image}__{port}"
    if settings.WITH_USERS:
        container_name += f"__{user_id}"

    command = f"{prefix}docker run -d -p {port}:80 --name {container_name} {docker_image}"

    # Start container
    try:
        output = subprocess.check_call(command, shell=True)
        if output != 0:
            return "Error starting docker", 500
    except subprocess.CalledProcessError:
        return "Error starting docker", 500

    # Set custom hash as id. The docker digest hash is 64 characters, a bit long
    container_hex = gen_random_hex_string(settings.HEX_SIZE)
    container_map[container_hex] = {
        "port": port,
        'image': docker_image
    }
    if settings.WITH_USERS:
        container_map[container_hex]["user_id"] = user_id

    update_proxy_config()

    return container_hex


@bp.route('/stop', methods=['POST'])
def stop_container():
    # Validate request parameters
    container_hex = request.form['container_hex']
    if container_hex == '':
        return "Bad request: no 'container_hex' is required", 400

    if container_hex not in container_map:
        return f"Error: docker container '{container_hex} does not exist!", 400

    data = container_map[container_hex]
    docker_image = data['image']
    port = data['port']

    container_name = f"{settings.CONTAINER_PREFIX}{docker_image}__{port}"
    if settings.WITH_USERS:
        user_id = data['user_id']
        container_name += f"__{user_id}"

    prefix = ""
    if not settings.WINDOWS:
        prefix = "sudo "

    command = f"{prefix}docker rm -f {container_name}"

    # Stop container
    try:
        output = subprocess.check_call(command, shell=True)
        if output != 0:
            return "Error stopping docker", 500
    except subprocess.CalledProcessError:
        return "Error stopping docker", 500

    # remove hex from map
    container_map.pop(container_hex)

    update_proxy_config()
    print(f"Removed container for docker image {docker_image} on port {port}")
    return "successfully removed docker"


@bp.route('/get_container_hex', methods=['GET'])
def get_container_hex():
    if settings.WITH_USERS == False:
        return "WITH_USERS is disabled!", 404

    user_id = request.args['user_id']

    container_hex = ''
    data = {}
    for hex, _data in container_map.items():
        print(_data)
        if _data['user_id'] == user_id:
            data = _data
            container_hex = hex

    if container_hex == '':
        return "Container not found for user", 404
    else:
        image_id = ''
        for key, val in settings.CONTAINER_IMAGES.items():
            if val == data['image']:
                image_id = key
                break

        return f"{container_hex}:{image_id}"


#           UTIL
# ==========================


def get_available_port() -> int:
    """Get an available port in the port range. Returns -1 if all ports are used."""
    used_ports = set([data['port'] for data in container_map.values()])
    all_ports = set(range(settings.PORT_START,
                    settings.PORT_START+settings.MAX_CONTAINERS))
    available_ports = all_ports.difference(used_ports)

    if len(available_ports) == 0:
        return -1
    else:
        return available_ports.pop()


def update_proxy_config():
    """see function name"""

    # create file if it doesn't exist
    if not exists(settings.PROXY_CONFIG):
        f = open(settings.PROXY_CONFIG, 'w+')
        f.close()

    # save the old configuration
    with open(settings.PROXY_CONFIG, 'r') as f:
        old_config = f.read()

    rewrite_rules: list[str] = []

    for hex, data in container_map.items():
        port = data['port']
        rule = f"""RewriteCond %{{HTTP_HOST}} ={hex}.{settings.DOMAIN}
RewriteRule ^/(.*) http://localhost:{port}/$1 [P,L]
ProxyPassReverse / http://localhost:{port}/"""
        rewrite_rules.append(rule)

    rewrite_rules_str = '\n\n'.join(rewrite_rules)
    new_file = f"""RewriteEngine On

{rewrite_rules_str}    

RewriteRule ^ - [L,R=404]"""

    with open(settings.PROXY_CONFIG, 'w') as f:
        f.write(new_file)

    # Reload apache
    if not settings.WINDOWS:
        try:
            subprocess.check_call('sudo systemctl reload apache2', shell=True)
        except subprocess.CalledProcessError:
            print('Reloading apache failed!')
            with open(settings.PROXY_CONFIG, 'w') as f:
                f.write(old_config)

            # old_config should not fail
            subprocess.check_call('sudo systemctl reload apache2')


def gen_random_hex_string(size):
    return ''.join(random.choices('0123456789abcdef', k=size))


def get_all_containers():
    """Run at startup to load all running contains that were spawned by the service into 
    `container_map`. Hex ids will be changed so call `update_proxy_config` next."""
    prefix = ""
    if not settings.WINDOWS:
        prefix = "sudo "

    command = f'{prefix}docker ps -a -f "name={settings.CONTAINER_PREFIX}"'

    try:
        output = subprocess.check_output(command)
    except subprocess.CalledProcessError:
        return

    containers = output.splitlines()
    if len(containers) == 1:
        return

    containers = containers[1:]

    # extract port and hex from the container name
    for docker_str in containers:
        # prefix + docker image + port + user id
        regex_str = "spawned__(.+)__(\d+)"
        if settings.WITH_USERS:
            regex_str += "__(\d+)"

        obj = re.search(regex_str, docker_str.decode())

        if settings.WITH_USERS:
            docker_image, port, user_id = obj.groups()
        else:
            docker_image, port = obj.groups()

        port = int(port)
        hex = gen_random_hex_string(settings.HEX_SIZE)

        container_map[hex] = {
            "port": port,
            "image": docker_image
        }
        if settings.WITH_USERS:
            container_map[hex]["user_id"] = user_id

    print(container_map)
