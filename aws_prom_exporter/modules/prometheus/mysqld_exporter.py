import logging

logger = logging.getLogger('aws-prom-exporter')


class Mysqld_exporter:

    data_attributes = ['endpoint', 'port', 'credentials', 'docker_image']
    default_docker_image = 'prom/mysqld-exporter'

    def __init__(self, data):
        self.refresh(data)

    def set_environment(self):
        self.environment = {
            'DATA_SOURCE_NAME': self.data_source_name(self.endpoint, self.port, self.credentials)
        }

    def data_source_name(self, endpoint, port, credentials):
        logger.debug('Set DATA_SOURCE_NAME for {} to {}:********@({}:{})/'.format(
            self.endpoint.split('.')[0], credentials['username'], endpoint, port))
        return '{}:{}@({}:{})/'.format(credentials['username'],
                                       credentials['password'], endpoint, port)

    def refresh(self, data):
        refreshed = False
        for attribute in self.data_attributes:
            try:
                attr = getattr(self, attribute)
                if attr != data[attribute]:
                    raise AttributeError
            except AttributeError:
                setattr(self, attribute, data[attribute])
                refreshed = True
            except KeyError:
                if attribute == 'docker_image':
                    setattr(self, attribute, default_docker_image)
                    refreshed = True
                    continue
                logger.error(
                    'Attribute {} expected in exporter data'.format(attribute))
                raise
        if refreshed:
            self.set_environment()

        return refreshed
