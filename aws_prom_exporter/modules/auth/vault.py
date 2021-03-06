import hvac
import json
import logging
import boto3

logger = logging.getLogger('aws-prom-exporter')


class VaultCredentialNotFound(Exception):
    pass


class VaultNotAuthenticated(Exception):
    pass


class Vault:

    database_cred = None

    def __init__(self, **kwargs):
        self.client = hvac.Client(kwargs)
        if not self.client.is_authenticated():
            # Try through IAM login
            try:
                credentials = boto3.Session().get_credentials()
                self.client.auth.aws.iam_login(
                    credentials.access_key, credentials.secret_key, credentials.token)
                if not self.client.is_authenticated():
                    raise Exception("Vault could not be authenticated")
            except hvac.exceptions.InvalidRequest:
                pass
            finally:
                if not self.client.is_authenticated():
                    raise VaultNotAuthenticated(
                        "Vault could not be authenticated")

    def get_database_cred(self, role):
        if self.database_cred:
            if self.renew_lease(self.database_cred['lease_id']):
                return self.database_cred['data']

        logger.debug('Getting a credential from Vault for {}'.format(role))
        try:
            response = self.client.adapter.get(
                '/v1/database/creds/{}'.format(role))
        except hvac.exceptions.InvalidRequest:
            raise VaultCredentialNotFound(
                "Was not possible to get database credentials for role '{}'".format(role))
        if response.status_code != 200:
            raise VaultCredentialNotFound(
                "Was not possible to get database credentials for role '{}'".format(role))
        self.database_cred = response.json()
        logger.debug('Got Vault lease {}'.format(
            self.database_cred['lease_id']))

        return self.database_cred['data']

    def renew_lease(self, lease):
        logger.debug('Renewing Vault lease {}'.format(lease))
        data = {'lease_id': lease}
        response = self.client.adapter.put(
            'v1/sys/leases/renew', data=json.dumps(data))
        if response.status_code != 200:
            return False
        return True
