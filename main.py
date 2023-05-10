from flask import Flask, request, Response
import requests
import os
from urllib.parse import urlparse

app = Flask(__name__)

CONTAINER_HOST = '127.0.0.1'

PORT_START = 9000
MAX_CONTAINERS = 3

container_images = {
    '1': 'challenge1'
}

# Mapping of hex IDs to container information
container_map = {
    # 'hex9000': {'user_id': '7', 'port': 9000}
    # 'hex_id_1': {'user_id': 0, 'port': 8000},
    # 'hex_id_2': {'user_id': 0, 'port': 9000},
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

    # f"docker run -d -p {new_port}:80 {docker_image}"
    container_map[f'hex{port}'] = {
        'user_id': request.form['user_id'],
        'port': port,
    }
    print(container_map)
    print(f"Starting container for docker image {docker_image} on port {port}")

    ok = os.system(f"docker run -d -p {port}:80 {docker_image}")
    if ok == 1:
        return "Error starting docker", 500
    
    # TODO: get docker hash and return that hash

    return f"http://{CONTAINER_HOST}:{port}"




def get_available_port() -> int:
    used_ports = set(container_info['port'] for container_info in container_map.values())
    all_ports = set(range(PORT_START, PORT_START+MAX_CONTAINERS))
    available_ports = all_ports.difference(used_ports)
    
    if len(available_ports) == 0:
        return -1
    else:
        return available_ports.pop()


if __name__ == '__main__':
    app.run()
