'''
Get users from managment devices
'''

import sys
assert sys.version_info.major == 3, 'For script run please use python3'
import logging
from nornir.core.filter import F
from nornir import InitNornir

import core_qtech_task
import core_routeros_task
import core_jun_task
import core_ios_task
import core_task



VAULT = 'inventory/creds.yaml'
PASSWORDVAULT = 'private/vault.passwd'


def configure_logging():
    '''
    Configure logging
    '''
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
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

    devices = list()
    devices.extend(core_ios_task.task_get_users(
        all_devices.filter(F(groups__contains="ios"))))
    devices.extend(core_jun_task.task_get_users(
        all_devices.filter(F(groups__contains="jun_srx"))))
    devices.extend(core_routeros_task.task_get_users(
        all_devices.filter(F(groups__contains="routeros"))))
    devices.extend(core_qtech_task.task_get_users(
        all_devices.filter(F(groups__contains="qtech"))))

    for device in devices:
        for user in device.users.keys():
            print("{}\t{}\t{}".format(
                device.hostname, user, device.users[user].keys()))

    logger.info("End program")


configure_logging()
if __name__ == "__main__":
    main()
