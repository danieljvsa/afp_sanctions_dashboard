import configparser

config = configparser.ConfigParser()
config.read('config.ini')


def parser_config(cfg):

    return config['env'][str(cfg)]