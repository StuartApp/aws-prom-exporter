#!/usr/bin/env python3

from modules.config import config
from modules.docker import Docker
from modules.nginx import Nginx
from modules.aws.rds import Rds
from modules.auth.vault import Vault, VaultCredentialNotFound
from modules.prometheus.mysqld_exporter import Mysqld_exporter
from modules.logs import logger
import time
import sys


def exception_hook(exctype, value, traceback):
    if exctype == KeyboardInterrupt:
        print(')CTRL-C captured, cleaning up')
    else:
        sys.__excepthook__(exctype, value, traceback)


sys.excepthook = exception_hook


logger.set_level(config.log_level)

# Setup Docker network
logger.debug('Setup Docker environment')
docker = Docker(network_name=config.docker_network_name)
docker.init()

# Start Nginx proxy
logger.debug('Setup Prometheus proxy')
nginx = Nginx(docker.network_name, config.nginx.docker_image, config.nginx.docker_name,
              config.nginx.listening_port, config.nginx.docker_port, config.nginx.config_file)
nginx.run()

vault_connections = {}
mysqld_exporters = {}

rds = Rds(id_filter=r'{}'.format(config.rds.search_regex))

logger.debug('Entering main loop')
while True:
    rds_info = rds.endpoints_by_group()
    instance_ids = []

    for group in rds_info:
        if group not in vault_connections:
            vault_connections[group] = Vault()

        try:
            creds = vault_connections[group].get_database_cred(
                '{}{}'.format(group, config.credentials.vault.role_suffix))
        except VaultCredentialNotFound:
            if config.credentials.skip_not_found:
                continue
            raise

        for instance in rds_info[group]:
            address = instance['Address']
            instance_id = address.split('.')[0]
            instance_ids.append(instance_id)
            port = instance['Port']

            if instance_id not in mysqld_exporters:
                mysqld_exporters[instance_id] = Mysqld_exporter(docker.network_name,
                                                                instance_id,
                                                                address, port,
                                                                creds,
                                                                config.mysqld_exporter.docker_image
                                                                )
                mysqld_exporters[instance_id].run()

            if mysqld_exporters[instance_id].credentials['username'] != creds['username'] or \
                    mysqld_exporters[instance_id].credentials['password'] != creds['password']:
                mysqld_exporters[instance_id].set_data_source_name(
                    address, port, creds)
                mysqld_exporters[instance_id].stop()
                mysqld_exporters[instance_id].run()

    # Old exporters cleanup
    for me in mysqld_exporters:
        if me not in instance_ids:
            mysqld_exporters[instance_id].stop()
            del mysqld_exporters[instance_id]

    time.sleep(config.loop_interval)
