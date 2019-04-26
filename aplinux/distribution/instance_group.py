# -*- codign:utf-8 -*-

from datetime import datetime

import logging


logger = logging.getLogger('aplinux.distribution')


def gce_cycle_instance_group(driver, instance_group_name, **kwargs):
    kwawrgs = kwargs.copy()

    # Generate instance temlate name from instance group name and timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    instance_template_name = f'{instance_group_name}-{timestamp}'

    # Ensure kwargs['ex_metadata']['items'] exists
    metadata = kwargs.setdefault('metadata', {})
    metadata.setdefault('items', [])

    # Read in a startup script from the filesystem
    if 'startup_script_path' in kwargs:
        startup_script = open(kwargs['startup_script_path'], 'r').read()
        metadata['items'].append({'key': 'startup-script',
                                  'value': startup_script})
        del kwargs['startup_script_path']  # remove this key from kwargs

    logger.info(f'Creating instance template {instance_template_name}')
    driver.ex_create_instancetemplate(instance_template_name, **kwargs)
    instance_template = driver.ex_get_instancetemplate(instance_template_name)

    logger.info('Setting {instance_group_name} instance group to new template...')
    instance_group = driver.ex_get_instancegroupmanager(instance_group_name)
    driver.ex_instancegroupmanager_set_instancetemplate(instance_group, instance_template)
