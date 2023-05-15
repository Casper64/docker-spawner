import subprocess
import datetime
import time
from .main import container_map, update_proxy_config
from . import settings

# docker inspect filters
raw_started_at = r"{{ .State.StartedAt }}"
raw_is_running = r"{{ .State.Running }}"


def cleanup_dockers(looping=True):
    """cleanup_dockers checks how long each docker container has been running.
    If it exceeds the maximum timeout defined the docker container will be removed."""
    while True:
        is_changed = False

        prefix = ""
        if not settings.WINDOWS:
            prefix = "sudo "

        # convert to list to avoid
        # RuntimeError: dictionary changed size during iteration
        items = list(container_map.items())
        for hex_stuff, data in items:
            docker_image = data['image']
            port = data['port']

            container_name = f"{settings.CONTAINER_PREFIX}{docker_image}__{port}"
            if settings.WITH_USERS:
                user_id = data['user_id']
                container_name += f"__{user_id}"

            # check if container is still running
            command = f'{prefix}docker inspect -f "{ raw_is_running }" {container_name}'
            try:
                output = subprocess.check_output(command, shell=True)
            except subprocess.CalledProcessError:
                print(
                    f'ERROR: could not get uptime for docker container "{container_name}" on port {port}')
                continue

            output = output.decode()
            if "false" in output:
                # container is no longer running
                remove_container(container_name, hex_stuff, port)
                is_changed = True
                continue

            command = f'{prefix}docker inspect -f "{ raw_started_at }" {container_name}'
            try:
                output = subprocess.check_output(command, shell=True)
            except subprocess.CalledProcessError:
                print(
                    f'ERROR: could not get uptime for docker container "{container_name}" on port {port}')
                continue

            timestamp = output.decode()
            # Docker returns more decimals in the seconds part and python can't handle that
            # so we need to cap it at max 26 characters
            timestamp = timestamp[:26]
            # According to rfc3339
            parsed_timestamp = datetime.datetime.strptime(
                timestamp, "%Y-%m-%dT%H:%M:%S.%f")
            # Get the current local time
            current_time = datetime.datetime.utcnow()
            # Calculate the time difference
            time_difference = current_time - parsed_timestamp
            time_difference_seconds = time_difference.total_seconds()

            if time_difference_seconds > settings.DOCKER_TIMEOUT:
                remove_container(container_name, hex_stuff, port)
                is_changed = True

        if is_changed:
            update_proxy_config()

        if not looping:
            return

        time.sleep(settings.CLEANUP_TIMEOUT)


def remove_container(container_name, hex_stuff, port):
    """remove_container does exactly what the function name implies :)"""
    prefix = ""
    if not settings.WINDOWS:
        prefix = "sudo "

    command = f"{prefix}docker rm -f {container_name}"
    try:
        subprocess.call(command, shell=True)
    except subprocess.CalledProcessError:
        print(
            f'ERROR: could not remove timed out docker container "{container_name}" on port {port}')
        return

    # remove container from map
    container_map.pop(hex_stuff)
    print(f'container "{container_name}" on port {port} timed out.')
