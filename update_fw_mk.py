# -*- coding: utf-8 -*-
'''
Module for update fw routeros devices
'''

import logging

from nornir import InitNornir
from nornir.core.filter import F
from packaging import version
import core_routeros_task
import core_task

VAULT = 'home-net/inventory/creds.yaml'
PASSWORDVAULT = 'home-net/private/vault.passwd'

def configure_logging():
    '''
    Configure logging
    '''
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(module)s - %(funcName)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)

def main():
    '''
    Main
    '''
    logger = logging.getLogger(__name__)
    logger.info("Start program for update fw RouterOS devices")

    logger.debug("Init nornir enviroment")
    all_devices = InitNornir(config_file="config.yaml")

    # Set auth information
    logger.debug('Fill access info from vault {}'.format(VAULT))
    core_task.init_creds(all_devices, VAULT, PASSWORDVAULT)

    logger.debug("Run task for get active/upgrade fw version")
    routeros_devices = all_devices.filter(F(groups__contains="routeros"))
    routeros_fw = core_routeros_task.task_get_routerboard(routeros_devices)
    for device in routeros_fw:
        if version.parse(device.currentfirmware) < version.parse(device.upgradefirmware):
            logger.info(f'Device {device.hostname} need update fw from {device.currentfirmware} to {device.upgradefirmware}')
            routeros_devices.inventory.hosts[device.hostname]['need_update'] = True
        else:
            routeros_devices.inventory.hosts[device.hostname]['need_update'] = False
    logger.info('Run update fw on devices')
    result = core_routeros_task.task_update_fw(routeros_devices.filter(need_update=True))
    for device in result['completed']:
        logger.info(f'FW was upgrade on {device} - need reboot for activate')
    for device in result['failed']:
        logger.error(f'FW not upgrade on {device} - check log')
    logger.info("End program for update fw. Please reboot devices manualy")

configure_logging()
if __name__ == "__main__":
    main()
