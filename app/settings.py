import platform

# Debug mode, turn off in linxu
WINDOWS = platform.system() == "Windows"

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
# Maximum time a docker container is allowed to run in seconds
DOCKER_TIMEOUT = 60 * 60
# How often the cleanup script has to be called, interval in seconds
CLEANUP_TIMEOUT = 60
# Enable if you want to use the `/get_container_hex` route and couple containers to a user id
WITH_USERS = True

# Add your container images here
CONTAINER_IMAGES: dict[str, str] = {
    # 'some_id': 'container_name'
    '1': 'challenge1',
    '2': 'challenge2'
}
