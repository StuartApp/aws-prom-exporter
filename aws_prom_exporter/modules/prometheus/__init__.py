from modules.config import config
import docker
import logging
from .file_sd import FileSD
import atexit

logger = logging.getLogger('aws-prom-exporter')


class Exporter:
    docker_client = None

    def __init__(self, name, exporter_type, data):
        self.docker_network = config.docker_network_name
        self.name = name
        self.docker_name = '{}-exporter-{}'.format(exporter_type, name)
        self.filesd = FileSD(
            config.prometheus.file_sd_path, name, exporter_type, 'localhost:{}'.format(config.nginx.docker_port))

        # Dynamically import exporter class based on its type
        exporter_module_name = '{}_exporter'.format(exporter_type)
        exporter_class_name = '{}_exporter'.format(exporter_type.capitalize())
        mod = __import__(exporter_module_name, globals=globals(), locals=locals(),
                         fromlist=[exporter_class_name], level=1)
        exporter_class = getattr(mod, exporter_class_name)

        self.exporter = exporter_class(data)
        atexit.register(self.stop)

    def run(self):
        if not self.docker_client:
            self.docker_client = docker.DockerClient()

        logger.debug(
            'Starting {} container using "{}" docker image'.format(
                self.docker_name, self.exporter.docker_image))
        self.container = self.docker_client.containers.run(
            image=self.exporter.docker_image,
            name=self.docker_name,
            environment=self.exporter.environment,
            detach=True,
            network=self.docker_network
        )
        self.filesd.write()

    def stop(self):
        logger.debug('Removing {}'.format(self.docker_name))
        self.container.remove(force=True)
        self.filesd.delete()

    def refresh(self, data):
        if self.exporter.refresh(data):
            self.stop()
            self.start()
