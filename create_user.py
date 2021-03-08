'''
Module for create user, account information define in script
'''
import logging
import sys
import argparse

from nornir.core.filter import F
from nornir import InitNornir

import core_qtech_task
import core_routeros_task
import core_jun_task
import core_ios_task
import core_task

assert sys.version_info.major == 3, 'For script run please use python3'

# set path to yaml and password file
VAULT = 'inventory/creds.yaml'
PASSWORDVAULT = 'private/vault.passwd'
CONFIG = "config.yaml"

# set mapping from groupname to called function
map_group_task_create_user = {'ios': core_ios_task.task_create_user,
                              'jun_srx': core_jun_task.task_create_user,
                              'routeros': core_routeros_task.task_create_user,
                              'qtech': core_qtech_task.task_create_user}

map_group_task_commit = {'jun_srx': core_jun_task.task_commit}

map_group_task_save_to_startup = {'ios': core_ios_task.task_save_to_startup,
                                  'qtech': core_qtech_task.task_save_to_startup}

map_group_task_get_users = {'ios': core_ios_task.task_get_users,
                            'jun_srx': core_jun_task.task_get_users,
                            'routeros': core_routeros_task.task_get_users,
                            'qtech': core_qtech_task.task_get_users}


# set auth password (for run this job)

def configure_logging():
    '''
    Configure logging
    '''
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
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

    logger.debug("Parse arguments")
    parser = argparse.ArgumentParser(description='Create new user on network devices')
    parser.add_argument('--username', '-u', action='store', required=True, help="New user name")
    parser.add_argument('--password', '-p', action='store', required=True, help="New user password")
    args = parser.parse_args()

    logger.debug("New username: %s", args.username)
    logger.debug("New username password: %s", args.password)

    logger.debug("Init nornir enviroment")
    all_devices = InitNornir(config_file=CONFIG)

    # Установка пароля
    logger.debug('Fill access info from vault {}'.format(VAULT))
    core_task.init_creds(all_devices, VAULT, PASSWORDVAULT)
 

    logger.info('Access to vault {}'.format(VAULT))
    groups_cred = core_task.read_vault(VAULT, PASSWORDVAULT)

    logger.info('Pre run check')
    devices = list()
    devices.extend(core_ios_task.task_get_users(
        all_devices.filter(F(groups__contains="ios"))))
    devices.extend(core_jun_task.task_get_users(
        all_devices.filter(F(groups__contains="jun_srx"))))
    devices.extend(core_routeros_task.task_get_users(
        all_devices.filter(F(groups__contains="routeros"))))
    devices.extend(core_qtech_task.task_get_users(
        all_devices.filter(F(groups__contains="qtech"))))

    logger.info('Check users')
    for device in devices:
        logger.debug('Check user {} in device {} exist'.format(args.username, device.hostname))
        if device.users.get(args.username):
            logger.warning('Skipping {}, user {} already exists'.format(device.hostname, args.username))
            all_devices.inventory.hosts[device.hostname]['error'] = True

    logger.info('Processing devices')
    for group in groups_cred.keys():
        logger.info('Run task create users on {} devices'.format(group))
        run_devices = all_devices.filter(F(error=False) & F(groups__contains=group))
        map_group_task_create_user[group](run_devices, args.username, args.password)
        logger.debug('Check device group {} need commit'.format(group))
        if group in map_group_task_commit.keys():
            map_group_task_commit[group](run_devices)
        logger.debug('Check device group {} need save to startup'.format(group))
        if group in map_group_task_save_to_startup.keys():
            map_group_task_save_to_startup[group](run_devices)

    logger.info('Post run check')
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
        logger.debug('Check user {} in device {} exist'.format(args.username, device.hostname))
        if device.users.get(args.username):
            logger.info('OK - User {} exists on device {}'.format(args.username, device.hostname))
        else:
            logger.error('User {} in device {} not was created'.format(args.username, device.hostname))

    logger.info("End program")


configure_logging()
if __name__ == "__main__":
    main()
