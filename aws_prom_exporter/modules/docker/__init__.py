import docker
import atexit
import logging

logger = logging.getLogger('mysqld_exporter')


class Docker:

    network = None

    def __init__(self, network_name, client=docker.DockerClient()):
        self.network_name = network_name
        self.client = client
        logger.debug('Registering cleanup at exit')
        atexit.register(self.cleanup)

    def init(self):
        logger.debug('Create {} network'.format(self.network_name))
        self.network = self.client.networks.create(self.network_name)

    def cleanup(self):
        if not self.network:
            return

        self.network = self.client.networks.get(self.network.id)
        logger.debug(
            'Deleting containers in network {}'.format(self.network_name))
        [x.remove(force=True) for x in self.network.containers]
        logger.debug('Deleting network {}'.format(self.network_name))
        self.network.remove()
