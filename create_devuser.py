'''
Module for create user, account information save on vault (YAML)
'''
import logging
import sys

from nornir.core.filter import F
from nornir import InitNornir

import core_qtech_task
import core_routeros_task
import core_jun_task
import core_ios_task
import core_task

assert sys.version_info.major == 3, 'For script run please use python3'

# set path to yaml and password file
VAULT = '/home/sas/home-net/inventory/creds.yaml'
PASSWORDVAULT = '/home/sas/home-net/private/vault.passwd'

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
PASSWORD = ""


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
    all_devices = InitNornir(config_file="/home/sas/home-net/config.yaml")

    # Установка пароля
    all_devices.inventory.defaults.password = PASSWORD

    logger.info('Access to vault {}'.format(VAULT))
    groups_cred = core_task.get_cred_from_vault(VAULT, PASSWORDVAULT)
    logger.debug('Fill new user parameters for groups in nornir inventory')
    for key, group in all_devices.inventory.groups.items():
        group['newuser_name'] = groups_cred[key]['username']
        group['newuser_password'] = groups_cred[key]['password']
        logger.debug('{} {} {}'.format(
            group.name, group['newuser_name'], group['newuser_password']))

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
        logger.debug('Check user {} in device {} exist'.format(
            all_devices.inventory.hosts[device.hostname]['newuser_name'], device.hostname))
        if device.users.get(all_devices.inventory.hosts[device.hostname]['newuser_name']):
            logger.warning('Skipping {}, user {} already exists'.format(
                device.hostname, all_devices.inventory.hosts[device.hostname]['newuser_name']))
            all_devices.inventory.hosts[device.hostname]['error'] = True

    logger.info('Processing devices')
    for group in groups_cred.keys():
        logger.info('Run task create users on {} devices'.format(group))
        map_group_task_create_user[group](all_devices.filter(error=False).filter(F(groups__contains=group)),
                                          groups_cred[group]['username'], groups_cred[group]['password'])
        logger.debug('Check device group {} need commit'.format(group))
        if group in map_group_task_commit.keys():
            map_group_task_commit[group](all_devices.filter(
                error=False).filter(F(groups__contains=group)))
        logger.debug(
            'Check device group {} need save to startup'.format(group))
        if group in map_group_task_save_to_startup.keys():
            map_group_task_save_to_startup[group](all_devices.filter(
                error=False).filter(F(groups__contains=group)))
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
        logger.debug('Check user {} in device {} exist'.format(
            all_devices.inventory.hosts[device.hostname]['newuser_name'], device.hostname))
        if device.users.get(all_devices.inventory.hosts[device.hostname]['newuser_name']):
            logger.info('OK - User {} exists on device {}'.format(
                all_devices.inventory.hosts[device.hostname]['newuser_name'], device.hostname))
        else:
            logger.error('User {} in device {} not was created'.format(
                all_devices.inventory.hosts[device.hostname]['newuser_name'], device.hostname))

    logger.info("End program")


configure_logging()
if __name__ == "__main__":
    main()
