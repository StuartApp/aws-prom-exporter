# AWS Prometheus Exporter
`aws-prom-exporter` is a program that discovers AWS resources and setup Prometheus exporters for them. It also setup a simple Nginx proxy so all exporters are accessible from one single port.

## Installation

Checkout the repository
Run on the base of the repository: `python setup.py install`

## Configuration

```yaml
# Log level
log_level: INFO
# Time between discoveries
loop_interval: 60
# Name of the docker network where all containers will be running in
docker_network_name: prometheus_rds

# RDS config
rds:
    # Regex to use when discovering RDS instances
    search_regex: '.*'
    # Suffix to use when getting credentials from Vault (`<rds_master_id><suffix>`)
    # It should match a Vault database role

# Credentials config
credentials:
    # What engine use by default to get credentials
    default_engine: vault
    # Vault specific configuration
    vault:
        # Vault role suffix to add to the master instance ID
        role_suffix: '-monitoring'
    # Wether to configure or not those discovered instances if credentials for them have not been discovered
    # If set to `false` it will throw an error if the credentials are not found
    skip_not_found: true

# Nginx config
nginx:
  # Image to use for the Nginx container
  docker_image: nginx
  # Container name for the Nginx proxy
  docker_name: mysqld-exporter-proxy
  # Nginx port to expose (will point to nginx_docker_port)
  docker_port: 9900
  # Nginx listening port inside the container
  listening_port: 80
  # Alternative full path of an nginx config file, if not defined or empty it will use a default one
  #config_file: ''

# MySQL exporter
mysqld_exporter:
  # Docker image to use for the MySQL exporter
  docker_image: prom/mysqld-exporter
```

## Run

Once installed, execute this command: `aws_prom_exporter`
It expects to found in the **same directory** you run it the configuration file (`config.yaml`), otherwise it will use the defaults.

## Supported AWS resources

* RDS:
	* MySQL: Both regular cluster and Aurora clusters are supported.

`aws-prom-exporter` expects to found configured credentials for AWS, either in `~/.aws/credentials` or as environment variables. Same way it is described [here](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html).

## Authentication

* Hashicorp Vault:
	* MySQL: [Vault database](https://www.vaultproject.io/docs/secrets/databases/index.html) setup needs to be done in advance for `aws-prom-exporter` to use it. Roles need to be named using the `rds_master_id` + the suffix set in the configuration: `credentials.vault.role_suffix`. Example, considering the setup suffix is `-monitoring` (the default) and the master ID is `production-cluster`:
      > `production-cluster-monitoring`

	`aws-prom-exporter` expects `VAULT_ADDR` and `VAULT_TOKEN` environment variables to be set and accessible.

## TODO

* Accept config file location as execution parameter.
* Support more AWS resources, like Elasticache
* Support more authentication methods, like simple (user:pass).
