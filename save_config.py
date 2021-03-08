'''
Module for get config from device and save to config dir
'''
import logging

from nornir import InitNornir
from nornir.core.filter import F

import core_task
#import core_ios_task
#import core_jun_task
import core_routeros_task
import core_qtech_task

VAULT = 'inventory/creds.yaml'
PASSWORDVAULT = 'private/vault.passwd'
CONFIGDIR = 'config'


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
    logger.info("Start program")

    logger.debug("Init nornir enviroment")
    all_devices = InitNornir(config_file="config.yaml")

    # Установка пароля
    logger.debug('Fill access info from vault {}'.format(VAULT))
    core_task.init_creds(all_devices, VAULT, PASSWORDVAULT)

    logger.debug("Run task for get config from device")

    core_task.task_get_napalm_config(all_devices.filter(F(groups__contains="ios")), 'startup', CONFIGDIR)
    core_qtech_task.task_get_config(all_devices.filter(F(groups__contains="qtech")),CONFIGDIR)
    core_task.task_get_napalm_config(all_devices.filter(F(groups__contains="jun_srx")), 'running', CONFIGDIR)
    core_routeros_task.task_get_export(all_devices.filter(F(groups__contains="routeros")), CONFIGDIR)
    core_routeros_task.task_get_bin_config(all_devices.filter(F(groups__contains="routeros")), CONFIGDIR)

    logger.info("End program")


configure_logging()
if __name__ == "__main__":
    main()
