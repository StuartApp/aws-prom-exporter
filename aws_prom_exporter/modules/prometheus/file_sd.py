import logging
from pathlib import Path
import yaml

logger = logging.getLogger('aws-prom-exporter')


class FileSD:

    def __init__(self, path, name, exporter_type, target):
        self.name = name
        self.exporter_type = exporter_type
        self.target = target

        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.filename = Path('{}_{}.yaml'.format(exporter_type, name))
        self.full_path_filename = self.path.joinpath(self.filename)

    def write(self):
        data = [
            {
                'labels': {
                    'type': self.exporter_type,
                    'instance': self.name,
                    'metrics_path': '/{}'.format(self.name)
                },
                'targets': [self.target]
            }
        ]
        self.full_path_filename.write_text(yaml.safe_dump(data))
        logger.debug('{} created'.format(self.full_path_filename))

    def delete(self):
        if self.full_path_filename.exists():
            self.full_path_filename.unlink()
            logger.debug('{} deleted'.format(self.full_path_filename))
