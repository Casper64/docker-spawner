from flask import Flask
from .main import get_all_running_containers, update_proxy_config

def create_app(test_config=None):
    get_all_running_containers()
    update_proxy_config()

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    from . import main
    app.register_blueprint(main.bp)

    return app

