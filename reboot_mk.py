# -*- coding: utf-8 -*-
'''
Module for update routeros devices
'''

import logging

from nornir import InitNornir
from nornir.core.filter import F
import core_routeros_task
import core_task

VAULT = 'inventory/creds.yaml'
PASSWORDVAULT = 'private/vault.passwd'
SCHED_TIMEOUT_SEC = 1*60 

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
    logger.info("Start program for schedule reboot RouterOS devices")

    logger.debug("Init nornir enviroment")
    all_devices = InitNornir(config_file="config.yaml")

    # Set auth information
    logger.debug('Fill access info from vault {}'.format(VAULT))
    core_task.init_creds(all_devices, VAULT, PASSWORDVAULT)

    logger.debug("Run task for create reboot task")
    routeros_info = core_routeros_task.task_schedule_reboot(
        all_devices.filter(F(groups__contains="routeros")).filter(F(reboot_last=False)),
        SCHED_TIMEOUT_SEC)

    logger.info(f"End program create reboot task. Devices will reboot at {SCHED_TIMEOUT_SEC} seconds")

configure_logging()
if __name__ == "__main__":
    main()
