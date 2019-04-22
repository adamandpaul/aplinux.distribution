# -*- coding:utf-8 -*-

import libcloud
import logging


logger = logging.getLogger('aplinux.distribution')


def gce_cycle_node(driver, node_name, **kwargs):

    logger.info(f'Cycling {node_name}')

    # tear down any current nodes
    try:
        current_node = driver.ex_get_node(node_name, kwargs.location)
    except libcloud.common.google.ResourceNotFoundError:
        current_node = None

    if current_node is not None:
        logger.info(f'Tearing down current {node_name}...')
        driver.destroy_node(current_node)

    ex_metadata = kwargs.setdefault('ex_metadata', {})
    ex_metadata.setdefault('items', [])

    # Substitute string external_ip to external_ip object
    if isinstance(kwargs.get('external_ip', None), str):
        kwargs['external_ip'] = driver.ex_get_address(config.external_ip)

    # Read in a startup script from the filesystem
    if 'startup_script_path' in kwargs:
        startup_script = open(kwargs['startup_script_path'], 'r').read()
        ex_metadata['items'].append({'key': 'startup-script',
                                     'value': startup_script})
        del kwargs['startup_script_path']

    logger.info(f'Booting new {node_name}...')
    driver.create_node(node_name, **kwargs)
