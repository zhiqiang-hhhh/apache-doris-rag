import configparser
import os

class Config:
    def __init__(self, config_file='conf.ini'):
        self.config = configparser.ConfigParser()
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file {config_file} not found.")
        self.config.read(config_file)

    @property
    def app(self):
        return self.config['app']

    @property
    def doris(self):
        return self.config['doris']

    @property
    def embedding(self):
        return self.config['embedding']

    @property
    def llm(self):
        return self.config['llm']

    @property
    def docs(self):
        return self.config['docs']

# Global configuration instance
settings = Config()
