class InvalidAppConfigurationException(Exception):

    def __init__(self, config_path: str, message: str):
        self.message = message
        self.config_path: str = config_path

    def __str__(self):
        return "Invalid application configuration {}. {}".format(self.config_path, self.message)
