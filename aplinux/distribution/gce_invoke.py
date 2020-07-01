# -*- coding:utf-8 -*-

from .node_manager import TemporyGCENode
from invoke import task
from datetime import datetime

import code
import json
import logging
import libcloud


logger = logging.getLogger('aplinux.distribution')


def get_driver(c):
    """Return the google cloud driver"""
    service_account = json.load(open(c.google_cloud.service_account_key_file, 'r'))
    driver_factory = libcloud.compute.providers.get_driver(libcloud.compute.types.Provider.GCE)
    return driver_factory(service_account['client_email'],
                          c.google_cloud.service_account_key_file,
                          datacenter=c.google_cloud.datacenter,
                          project=c.google_cloud.project_id,
                          timeout=300)


def new_image_name(c):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f'{c.target_image_prefix}{timestamp}'


@task
def build(c):
    """Build an image"""
    import fabfile
    logger.info('Build a fresh new image.')
    driver = get_driver(c)
    kwargs = {**c.google_cloud.node_defaults, **c.build_node}
    with TemporyGCENode(driver, fabric_config_defaults=c.fabric, **kwargs) as nm:
        fabfile.build(nm.fabric)
        nm.stop_and_create_image(new_image_name(c))


@task
def init(c):
    """Run only init on an image"""
    import fabfile
    logger.info('Build a fresh new image.')
    driver = get_driver(c)
    kwargs = {**c.google_cloud.node_defaults, **c.build_node}
    with TemporyGCENode(driver, fabric_config_defaults=c.fabric, **kwargs) as nm:
        fabfile.init(nm.fabric)
        nm.stop_and_create_image(new_image_name(c))


@task
def update(c):
    """Update an image"""
    import fabfile
    logger.info('Build an updated image from the most recent image.')
    driver = get_driver(c)
    kwargs = {**c.google_cloud.node_defaults, **c.update_node}
    with TemporyGCENode(driver, fabric_config_defaults=c.fabric, **kwargs) as nm:
        fabfile.update(nm.fabric)
        nm.stop_and_create_image(new_image_name(c))
        

@task
def quick_update(c):
    """Quickly Update an image"""
    import fabfile
    logger.info('Build an quickly updated image from the most recent image.')
    driver = get_driver(c)
    kwargs = {**c.google_cloud.node_defaults, **c.update_node}
    with TemporyGCENode(driver, fabric_config_defaults=c.fabric, **kwargs) as nm:
        fabfile.quick_update(nm.fabric)
        nm.stop_and_create_image(new_image_name(c))


@task
def cli(c, tempory_node=False):
    import fabfile
    import tasks
    driver = get_driver(c)
    local = {'c': c,
             'driver': driver,
             'fabfile': fabfile,
             'tasks': tasks,
             'nm': None}
    banner = '\n'.join(('cli available vars:',
                        '    c: current invoke config',
                        '    driver: libcloud driver from config',
                        '    fabfile: fabfile module from fabfile.py',
                        '    tasks: tasks module from tasks.py',
                        '    nm: node manager if run with -t/--tempory-node'))
    if tempory_node:
        kwargs = {
            **c.google_cloud.node_defaults,
            **c.cli_node,
        }
        with TemporyGCENode(driver, **kwargs) as nm:
            local['nm'] = nm
            code.interact(banner=banner, local=local)
    else:
        code.interact(banner=banner, local=local)
