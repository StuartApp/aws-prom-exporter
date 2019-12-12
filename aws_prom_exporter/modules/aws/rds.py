import boto3
import re
import logging

logger = logging.getLogger('mysqld_exporter')


class Rds:

    instances = []
    clusters = []
    classic_engine_filters = {}
    aurora_engine_filters = {}

    def __init__(self, id_filter=None, engine=None):
        self.client = boto3.client('rds')
        self.id_filter = self._check_re(id_filter)
        if engine:
            self.classic_engine_filters = [{'Name': 'engine', 'Value': engine}]
            self.aurora_engine_filters = [
                {'Name': 'engine', 'Value': 'aurora-{}'.format(engine)}]

    def _check_re(self, re_object, default=None):
        if hasattr(re_object, 'pattern'):
            return re_object
        if isinstance(re_object, str):
            return re.compile(re_object)
        if not default:
            return re.compile(r'.*')
        return self._check_re(default)

    def _merge_filters(self, filters_a, filters_b):
        filters = []
        for fa in filters_a:
            for fb in filters_b:
                if fb['Name']:
                    fa['Value'] == fb['Value']
            filters.append(fa)
        return filters

    def discover_instances(self, filters=[], id_filter=None):
        marker = ""
        new_instances = []

        self.classic_engine_filters = self._merge_filters(
            self.classic_engine_filters, filters)
        id_filter = self._check_re(id_filter, self.id_filter)

        while True:
            paginator = self.client.get_paginator('describe_db_instances')
            iterator = paginator.paginate(
                Filters=self.classic_engine_filters,
                Marker=marker)
            for page in iterator:
                for instance in page['DBInstances']:
                    if 'DBClusterIdentifier' not in instance:  # Discard Aurora
                        if 'ReadReplicaSourceDBInstanceIdentifier' in instance and \
                                id_filter.match(instance['ReadReplicaSourceDBInstanceIdentifier']):
                            new_instances.extend([instance])
                        if id_filter.match(instance['DBInstanceIdentifier']):
                            new_instances.extend([instance])
            try:
                marker = page['Marker']
            except KeyError:
                break
        self.instances = new_instances
        return self.instances

    def get_db_instance_masters(self):
        masters = []

        if not self.instances:
            self.discover_instances(id_filter=self.id_filter)

        for instance in self.instances:
            if not 'ReadReplicaSourceDBInstanceIdentifier' in instance:
                masters.append(instance['DBInstanceIdentifier'])
        return masters

    def get_db_instance_replicas(self, master_id=None):
        replicas = []

        if not self.instances:
            self.discover_instances(id_filter=self.id_filter)

        for instance in self.instances:
            if 'ReadReplicaSourceDBInstanceIdentifier' in instance:
                if not master_id or instance['ReadReplicaSourceDBInstanceIdentifier'] == master_id:
                    replicas.append(instance['DBInstanceIdentifier'])

        return replicas

    def get_instance_by_identifier(self, identifier):
        if not self.instances:
            self.discover_instances(id_filter=self.id_filter)

        for instance in self.instances:
            if instance['DBInstanceIdentifier'] == identifier:
                return instance

        return None

    def discover_clusters(self, filters=[], id_filter=None):
        marker = ""
        new_clusters = []

        id_filter = self._check_re(id_filter, self.id_filter)

        self.aurora_engine_filters = self._merge_filters(
            self.aurora_engine_filters, filters)

        while True:
            paginator = self.client.get_paginator('describe_db_clusters')
            iterator = paginator.paginate(
                Filters=self.aurora_engine_filters,
                Marker=marker)
            for page in iterator:
                for cluster in page['DBClusters']:
                    if id_filter.match(cluster['DBClusterIdentifier']):
                        new_clusters.extend([cluster])
            try:
                marker = page['Marker']
            except KeyError:
                break
        self.clusters = new_clusters
        return self.clusters

    def get_clusters(self):
        clusters = []

        if not self.clusters:
            self.discover_clusters(id_filter=self.id_filter)

        for cluster in self.clusters:
            clusters.append(cluster['DBClusterIdentifier'])

        return clusters

    def get_cluster_instances(self, cluster_id):
        marker = ""
        instances = []

        while True:
            paginator = self.client.get_paginator('describe_db_instances')
            iterator = paginator.paginate(
                Marker=marker)
            for page in iterator:
                for instance in page['DBInstances']:
                    if 'DBClusterIdentifier' in instance and instance['DBClusterIdentifier'] == cluster_id:
                        instances.extend([instance])
            try:
                marker = page['Marker']
            except KeyError:
                break
        return instances

    def get_all_instances(self):
        instances = self.discover_instances()
        for cluster in self.discover_clusters():
            instances.extend(self.get_cluster_instances(
                cluster['DBClusterIdentifier']))
        return instances

    def endpoints_by_group(self):
        endpoints = {}
        logger.debug(
            'Fetch RDS instances using "{}" filter'.format(self.id_filter.pattern))
        for master in self.get_db_instance_masters():
            endpoints[master] = []
            endpoints[master].append(
                self.get_instance_by_identifier(master)['Endpoint'])

            for replica in self.get_db_instance_replicas(master):
                endpoints[master].append(self.get_instance_by_identifier(
                    replica)['Endpoint'])
        for cluster in self.get_clusters():
            endpoints[cluster] = [x['Endpoint']
                                  for x in self.get_cluster_instances(cluster)]
        logger.debug('RDS instances discovered: {}'.format(endpoints))
        return endpoints
