from flask import Flask, request, Response
import requests

app = Flask(__name__)

CONTAINER_HOST = '127.0.0.1'

# Mapping of hex IDs to container information
container_map = {
    'hex_id_1': {'user_id': 0, 'port': 8000},
    'hex_id_2': {'user_id': 0, 'port': 9000}
}

@app.route('/container/<hex_id>', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/container/<hex_id>/<path:path>', methods=['GET', 'POST'])
def handle_container_request(hex_id, path):
    if hex_id in container_map:
        container_info = container_map[hex_id]
        container_port = container_info['port']
        container_url = f'http://{container_host}:{container_port}/{path}'

        # Preserve the original HTTP method and forward the request
        response = requests.request(
            method=request.method,
            url=container_url,
            headers=request.headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=True  # Allow redirects
        )

        # Modify the response before returning it to the client
        proxied_response = Response(response.content, response.status_code, headers=response.headers.items())
        
        # If the response is a redirect, modify the location header
        if response.is_redirect:
            # Modify the redirect URL to hide the container URL
            modified_location = '/container/' + hex_id + '/' + response.headers['Location']
            proxied_response.headers['Location'] = modified_location
        
        return proxied_response

    return 'Hex ID not found', 400

@app.route('/spawn', methods=['POST'])
def create_container():

    return 'hex id'

if __name__ == '__main__':
    app.run()
