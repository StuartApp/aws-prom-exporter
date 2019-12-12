import setuptools
import os

packages = []

for root, directory, files in os.walk('./aws_prom_exporter/'):
    if '__init__.py' in files:
        packages.append(os.path.relpath(root, './aws_prom_exporter/'))

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='aws_prom_exporter',
    install_requires=[
        'docker', 'pyyaml', 'boto3', 'hvac'
    ],
    scripts=['bin/aws-prom-exporter'],
    version='0.1',
    author="Jordi Clariana",
    author_email="j.clariana@stuart.com",
    description="Dynamically create Prometheus exporters for AWS resources like RDS or Elasticache",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/StuartApp/aws-prom-exporter",
    packages=packages,
    package_dir={'': 'aws_prom_exporter'},
    package_data={'': ['data/config.yaml', 'data/nginx.conf']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)
