import docker
import logging

logger = logging.getLogger('mysqld_exporter')


class Mysqld_exporter:

    docker_client = None

    def __init__(self, docker_network, name, endpoint, port, credentials, docker_image):
        self.docker_network = docker_network
        self.name = 'mysqld-exporter-{}'.format(name)
        self.endpoint = endpoint
        self.port = port
        self.credentials = credentials
        self.set_data_source_name(
            endpoint, port, credentials)
        self.docker_image = docker_image

    def run(self):
        if not self.docker_client:
            self.docker_client = docker.DockerClient()

        logger.debug(
            'Starting {} container using "{}" docker image'.format(self.name, self.docker_image))
        self.container = self.docker_client.containers.run(
            image=self.docker_image,
            name=self.name,
            environment={
                'DATA_SOURCE_NAME': self.data_source_name
            },
            detach=True,
            network=self.docker_network
        )

    def stop(self):
        logger.debug('Removing {}'.format(self.name))
        self.container.remove(force=True)

    def set_data_source_name(self, endpoint, port, credentials):
        logger.debug('Set DATA_SOURCE_NAME for {} to {}:********@({}:{})/'.format(
            self.name, credentials['username'], endpoint, port))
        self.data_source_name = '{}:{}@({}:{})/'.format(credentials['username'],
                                                        credentials['password'], endpoint, port)
