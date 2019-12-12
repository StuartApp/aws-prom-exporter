from .config import Config
import yaml
import logging

logger = logging.getLogger('mysqld_exporter')

config_defaults = {
    'rds': {
        'search_regex': '.*',

    },
    'credentials': {
        'default_engine': 'vault',
        'vault': {
            'role_suffix': '-monitoring',
        },
        'skip_not_found': True,
    },
    'log_level': 'INFO',
    'loop_interval': 60,
    'docker_network_name': 'prometheus_rds',
    'nginx': {
        'docker_image': 'nginx',
        'docker_name': 'mysqld-exporter-proxy',
        'docker_port': 9900,
        'listening_port': 80,
        'config_file': None,
    },
    'mysqld_exporter': {
        'docker_image': 'prom/mysqld-exporter',
    }
}


def load_config():
    try:
        with open('config.yaml') as f:
            logger.debug('Config file config.yaml loaded')
            return yaml.safe_load(f)
    except IOError:
        logger.debug('config.yaml not found, using defaults')
        return {}


config_custom = load_config()
config = Config(config_defaults, config_custom).generate()
