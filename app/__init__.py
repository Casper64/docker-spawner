from flask import Flask
from .main import get_all_containers, update_proxy_config
from .cleanup import cleanup_dockers
import threading


def create_app(test_config=None):
    get_all_containers()
    update_proxy_config()

    # run `cleanup_dockers` in a seperate thread
    thread = threading.Thread(target=cleanup_dockers)
    thread.daemon = True
    thread.start()

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    from . import main
    app.register_blueprint(main.bp)

    return app
