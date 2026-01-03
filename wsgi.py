from werkzeug.middleware.proxy_fix import ProxyFix

from flask_application import create_app

flask_app = create_app()

if flask_app:
    application = ProxyFix(flask_app, x_for=1, x_proto=1)

