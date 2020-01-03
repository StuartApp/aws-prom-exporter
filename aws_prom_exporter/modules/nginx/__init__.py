import docker
import os
import logging

logger = logging.getLogger('aws-prom-exporter')


class Nginx:

    docker_client = None

    def __init__(self, docker_network, docker_image, docker_name,
                 docker_internal_port, docker_published_port, nginx_config_file):
        self.docker_network = docker_network
        self.docker_image = docker_image
        self.docker_name = docker_name
        self.docker_internal_port = docker_internal_port
        self.docker_published_port = docker_published_port
        self.nginx_config_file = nginx_config_file

    def run(self):
        if not self.docker_client:
            self.docker_client = docker.DockerClient()

        if not self.nginx_config_file:
            nginx_config_file = "{}/../../data/nginx.conf".format(
                os.path.dirname(os.path.realpath(__file__)))
        logger.debug(
            'Using {} config file for Nginx'.format(nginx_config_file))

        logger.debug('Starting Nginx container')
        self.docker_client.containers.run(
            image=self.docker_image,
            name=self.docker_name,
            detach=True,
            ports={'{}/tcp'.format(self.docker_internal_port)
                                   : self.docker_published_port},
            volumes={nginx_config_file: {
                'bind': '/etc/nginx/nginx.conf', 'mode': 'ro'}},
            network=self.docker_network
        )
