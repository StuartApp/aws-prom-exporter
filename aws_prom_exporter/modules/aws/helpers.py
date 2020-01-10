import requests
import os
from requests.packages.urllib3 import Retry
import boto3


class NotEC2Instance(Exception):
    pass


def get_region():
    region = boto3.session.Session().region_name
    if not region:
        return get_instance_region()
    return region


def get_instance_region():
    instance_identity_url = "http://169.254.169.254/latest/dynamic/instance-identity/document"
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.3)
    metadata_adapter = requests.adapters.HTTPAdapter(max_retries=retries)
    session.mount("http://169.254.169.254/", metadata_adapter)
    try:
        r = requests.get(instance_identity_url, timeout=(2, 5))
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as err:
        print("Connection to AWS EC2 Metadata timed out: " +
              str(err.__class__.__name__))
        print(
            "Is this an EC2 instance? Is the AWS metadata endpoint blocked? (http://169.254.169.254/)")
        raise NotEC2Instance
    response_json = r.json()
    region = response_json.get("region")
    return region
