from flask import Flask, request
import subprocess
import random

app = Flask(__name__)

CONTAINER_HOST = '127.0.0.1'

PORT_START = 9000
MAX_CONTAINERS = 3
PROXY_CONFIG = 'dynamic_proxy.conf'
DOMAIN = 'anonymousctf.com'

container_images = {
    '1': 'challenge1'
}

# Mapping of hex IDs to container information
container_map = {
    # 'hex9000': 9000
}


@app.route('/spawn', methods=['POST'])
def create_container():
    challenge_id = request.form['challenge_id']
    if challenge_id == '':
        return "Bad request: no 'challenge_id' is required", 400

    if challenge_id not in container_images:
        return f"Error: docker image for challenge id does not exist!", 400

    if (port := get_available_port()) == -1:
        return f"Error: max available containers reached!", 400

    docker_image = container_images[challenge_id]

    print(f"Starting container for docker image {docker_image} on port {port}")

    try:
        output = subprocess.check_call(
            f"docker run -d -p {port}:80 {docker_image}", shell=True)
        if output != 0:
            return "Error starting docker", 500
    except subprocess.CalledProcessError:
        return "Error starting docker", 500

    # only get 16 characters since 64 is a bit long
    container_digest = gen_random_hex_string(32)
    container_map[container_digest] = port
    print(container_map)

    # TODO: update dynamic_proxy.conf
    update_proxy_config()

    return container_digest


def get_available_port() -> int:
    used_ports = set(container_map.values())
    all_ports = set(range(PORT_START, PORT_START+MAX_CONTAINERS))
    available_ports = all_ports.difference(used_ports)
    print(used_ports, all_ports, available_ports)

    if len(available_ports) == 0:
        return -1
    else:
        return available_ports.pop()


def update_proxy_config():
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

    # try:
    #     subprocess.check_call('sudo systemctl reload apache2')
    # except subprocess.CalledProcessError:
    #     print('apache failed :(')
    #     with open(PROXY_CONFIG, 'w') as f:
    #         f.write(old_config)

    #     subprocess.check_call('sudo systemctl reload apache2')

def gen_random_hex_string(size):
    return ''.join(random.choices('0123456789abcdef', k=size))

if __name__ == '__main__':
    app.run()
