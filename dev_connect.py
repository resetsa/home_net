# -*- coding: utf-8 -*-
'''
Module for check connect to this user credentials in VAULT
'''

import logging

from nornir import InitNornir
from nornir.core.filter import F

import core_task
import core_ios_task
import core_jun_task
import core_routeros_task
import core_qtech_task

VAULT = 'inventory/creds.yaml'
PASSWORDVAULT = 'private/vault.passwd'


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
    logger.info("Start program for config network")

    logger.debug("Init nornir enviroment")
    all_devices = InitNornir(config_file="config.yaml")

    # Установка пароля
    logger.debug('Fill access info from vault {}'.format(VAULT))
    core_task.init_creds(all_devices, VAULT, PASSWORDVAULT)

    logger.debug("Run task for get os version")
    routeros = core_routeros_task.task_get_info(
        all_devices.filter(F(groups__contains="routeros")))
    qtech = core_qtech_task.task_get_info(
        all_devices.filter(F(groups__contains="qtech")))
    ios = core_ios_task.task_get_info(
        all_devices.filter(F(groups__contains="ios")))
    jun_srx = core_jun_task.task_get_info(
        all_devices.filter(F(groups__contains="jun_srx")))

    logger.info("End program for config network")

    for device in routeros:
        print("Hostname is {} \t ROS \t {}".format(
            device.hostname, device.version))
    for device in qtech:
        print("Hostname is {} \t Qtech \t {}".format(
            device.hostname, device.version))
    for device in ios:
        print("Hostname is {} \t IOS \t {}".format(
            device.hostname, device.version))
    for device in jun_srx:
        print("Hostname is {} \t JunOS \t {}".format(
            device.hostname, device.version))


configure_logging()
if __name__ == "__main__":
    main()
