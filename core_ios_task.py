# -*- coding: utf-8 -*-
'''
Module for ios task and functions
'''
import logging
import sys
assert sys.version_info.major == 3, 'For script run please use python3'
from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko.tasks import netmiko_send_command
from nornir_netmiko.tasks import netmiko_send_config
from nornir_utils.plugins.functions import print_result
from nornir_netmiko.tasks import netmiko_save_config
from nornir.core.task import Task

from core_task import create_info_tuple


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


def parse_info(hostname, dict_prop):
    '''
    Create object from hostname, info
    '''
    result = None
    dict_out = dict()
    dict_out['hostname'] = hostname
    dict_out['model'] = dict_prop[0]['hardware']
    dict_out['version'] = dict_prop[0]['version']
    dict_out['image'] = dict_prop[0]['running_image']
    dict_out['serial'] = dict_prop[0]['serial'][0]
    dict_out['uptime'] = dict_prop[0]['uptime']
    result = create_info_tuple(dict_out)
    return result


def parse_users(hostname, dict_users):
    '''
    Create object from hostname, dict_user
    '''
    result = None
    result = None
    dict_out = dict()
    dict_out['hostname'] = hostname
    dict_out['users'] = dict()
    for user, user_prop in dict_users.items():
        dict_out['users'][user] = user_prop
    result = create_info_tuple(dict_out)
    return result


def task_get_info(task: Task):
    """
    Function for get IOS version
    Output - list of object, present IOS device
    """
    logger = logging.getLogger(__name__)
    logger.debug('Get IOS version')
    result = list()
    out = task.run(task=netmiko_send_command,
                   command_string="show version", use_textfsm=True)
#    print_result(out)
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning(f'Failed task on device {host}')
            task.inventory.hosts[host]['error'] = True
    for host, res in out.items():
        if not res.failed:
            logger.debug(f'Fill IOS properties {host}')
            task.inventory.hosts[host]['error'] = False
#            with open('output/qtech_show_version.txt','w+') as f:
#                f.write(r.result)
            result.append(parse_info(host, res.result))
    return result


def task_get_users(task: Task):
    """
    Function for get user from IOS
    Output - list of object, present IOS device with users
    """
    logger = logging.getLogger(__name__)
    logger.debug('Get IOS users info')
    result = list()
    out = task.run(napalm_get, getters=['get_users'])
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning('Failed task on device {}'.format(
                task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = True
    for host, res in out.items():
        if not res.failed:
            logger.debug('Fill IOS users properties from device {}'.format(
                task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = False
#            with open('output/qtech_show_version.txt','w+') as f:
#                f.write(r.result)
            result.append(parse_users(host, res.result['get_users']))
    return result


def task_create_user(task: Task, username, password, priv=15):
    """
    Function for create user, default with 15 priviledges
    Output - dict {'completed':[], 'failed':[]}
    """
    logger = logging.getLogger(__name__)
    logger.debug('Create user')
    config_commands = ["username {} privilege {} secret {}".format(
        username, priv, password)]
    logger.debug(config_commands)
    result = {'completed': [], 'failed': []}
    out = task.run(task=netmiko_send_config, config_commands=config_commands)
    print_result(out)
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning('Failed task on device {}'.format(
                task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = True
            result['failed'].append(host)
    for host, res in out.items():
        if not res.failed:
            logger.debug('Create user {} with device {} '.format(
                username, task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = False
            result['completed'].append(host)
#            result.append(parse_info(h,r.result))
    return result


def task_save_to_startup(task: Task):
    """
    Function for save running config to startup config
    Output - dict {'completed':[], 'failed':[]}
    """
    logger = logging.getLogger(__name__)
    logger.debug('Save running config to startup config')
    result = {'completed': [], 'failed': []}
    out = task.run(task=netmiko_save_config,
                   cmd='copy running-config startup-config', confirm=True, confirm_response="")
    print_result(out)
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning('Failed task on device {}'.format(
                task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = True
    for host, res in out.items():
        if not res.failed:
            logger.debug('Save config on device {}'.format(task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = False
            result['completed'].append(host)
    return result


def main():
    '''
    Main
    '''
    logger = logging.getLogger(__name__)
    logger.info('Start script')
    logger.info('End script')


configure_logging()
if __name__ == "__main__":
    main()
