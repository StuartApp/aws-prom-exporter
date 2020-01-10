#!/usr/bin/env python3

from modules.config import config
from modules.docker import Docker
from modules.nginx import Nginx
from modules.aws.rds import Rds
from modules.auth.vault import Vault, VaultCredentialNotFound
from modules.prometheus import Exporter
from modules.logs import logger
import time
import sys
import signal

vault_connections = {}
mysqld_exporters = {}


def exit_gracefully(signum, frame):
    sys.exit(0)


signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)

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
            data = {}
            data['endpoint'] = instance['Address']
            data['port'] = instance['Port']
            data['credentials'] = creds
            data['docker_image'] = config.prometheus.exporter.mysqld.docker_image
            instance_id = data['endpoint'].split('.')[0]
            instance_ids.append(instance_id)

            if instance_id not in mysqld_exporters:
                # Create new exporters
                mysqld_exporters[instance_id] = Exporter(instance_id,
                                                         'mysqld',
                                                         data
                                                         )
                mysqld_exporters[instance_id].run()

            # Refresh exporter credentials if they have changed
            mysqld_exporters[instance_id].refresh(data)

    # Old exporters cleanup
    for me in mysqld_exporters:
        if me not in instance_ids:
            mysqld_exporters[instance_id].stop()
            del mysqld_exporters[instance_id]

    time.sleep(config.loop_interval)
