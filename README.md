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
git clone https://github.com/Casper64/docker-container-spawner docker-spawner
cd docker-container-spawner
```

### Python

To setup the server first create a virtual environment and then install the packages.

**Linux example:**

```bash
python -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
```

### Port ranges

`PORT_START` and `MAX_CONTAINERS` will set the range of ports where docker containers
can be spawned:

Port range = `[PORT_START - (PORT_START + MAX_CONTAINERS)]`

### Container images

`CONTAINER_IMAGES` is a dict where the value is the name of a docker container and
the key is the id that will be check when you post to `/spawn`.

You can customize all other constants in `main.py`.

## Dynamic subdomain

In order to use Docker Spawner you need to have a [wildcard DNS record][^1] for your domain.

In `apache.conf` is a default configuration for Apache which you can extend. Make sure to always
include the `Include` rule and update the default values.

## Usage
Run the app with flask from your virtual environment or [run it as a service].
```bash
flask --app main.py run
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
```

<!-- Links -->
[^1]: https://en.wikipedia.org/wiki/Wildcard_DNS_record

