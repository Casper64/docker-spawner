# Docker Spawner

Docker Spawner is a service which lets you start and stop docker containers on
demand via an http-endpoint and mount them to a dynamic subdomain.

## Features

-   Http endpoints
-   Reverse proxy from subdomain to docker container
-   Configured for Apache

## Installation

Clone the repository and navigate to the folder

```bash
git clone https://github.com/Casper64/docker-spawner
cd docker-spawner
```

## Python

To setup the server first create a virtual environment and then install the packages.

**Linux example:**

```bash
python -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
```

## Dynamic subdomain

In order to use Docker Spawner you need to have a [wildcard DNS record](^1) for your domain.

In `apache.conf` is a default configuration for Apache which you can extend. Make sure to always
include the `Include` rule and update the default values.

## Usage

Replace `YOUR_PORT` and run the app with flask from your virtual environment or
[run it as a service](#systemd-service).

```bash
flask --app app run --port=YOUR_PORT
```

## Systemd Service

You can also run Docker Spawner as a service on your server.

### Setup

Change the default values in `docker-spawner.service`.

Copy `docker-spawner.service` to your `systemd` folder.

```bash
sudo cp docker-spawner.service /etc/systemd/service
```

Reload the systemd daemon to load the service.

```bash
sudo systemctl daemon-reload
```

Enable and start the service at startup.

```bash
sudo systemctl enable docker-spawner
sudo systemctl start docker-spawner
```

## Endpoints

### Start a docker container: `POST /spawn`

Required form data:

-   `container_id`: the id of the container specified in `CONTAINER_IMAGES`
-   `user_id`: the users is, when [users support](#users-support) is enabled

Returns
Returns `HTTP 4xx` with an error message if the request failed.

### Stop a docker container: `POST /stop`

Required form data:

-   `container_hex`: the hex identifer of the docker container. You can obtain it from `/spawn`

### Get hex from a container by user id

> **Note**: this route is only enabled when [users support](#users-support) is enabled

required form data

-   `user_id`: the users id

## Settings

You can edit the configuration in `app/settings.py`.

### Port ranges

`PORT_START` and `MAX_CONTAINERS` will set the range of ports where docker containers
can be spawned:

Port range = `[PORT_START, (PORT_START + MAX_CONTAINERS)]`

### Container images

`CONTAINER_IMAGES` is a dict where the value is the name of a docker container and
the key is the id that will be check when you post to `/spawn`.

You can customize all other constants in `main.py`.

### Users Support

You can couple a docker container to a user. User support is enabled by default.
To disable it set `WITH_USERS` to `False`.

> **Note**: user support assumes that only 1 user can have a docker container
> active at all time, but this isn't verified!

When user support is enable the `/get_container_hex` endpoint becomes available.

You can view the other configuration options in `app/settings.py`.

<!-- Links -->

[^1]: https://en.wikipedia.org/wiki/Wildcard_DNS_record
