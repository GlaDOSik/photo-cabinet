from flask_application import create_app

if __name__ == "__main__":
    app = create_app()

    if app:
        app.run(host="localhost",
                port="5000",
                debug=False)
