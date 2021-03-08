'''
Modules with task and functions for JunOS
'''

import logging
import sys
assert sys.version_info.major == 3, 'For script run please use python3'

import crypt
import textfsm
from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko.tasks import netmiko_send_command
from nornir_utils.plugins.functions import print_result
from nornir_netmiko.tasks import netmiko_send_config
from nornir_netmiko.tasks import netmiko_commit
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


def parse_info(hostname, dict_props):
    '''
    Create object from hostname,dict_props
    '''
    result = None
    dict_out = dict()
    dict_out['hostname'] = hostname
    dict_out['version'] = dict_props[0]['other_properties_versions'][0]
#    result = DeviceData(**dict_out)
    result = create_info_tuple(dict_out)
    return result


def parse_users(hostname, dict_users):
    '''
    Create object from users info
    '''
    result = None
    template_file_path = 'templates/jun_show_conf_system_login.template'
    dict_out = dict()
    with open(template_file_path) as template:
        fsm = textfsm.TextFSM(template)
        dict_out['hostname'] = hostname
        dict_out['users'] = dict()
        for user in fsm.ParseText(dict_users):
            temp_dict = dict(zip(fsm.header, user))
            username = temp_dict.pop('username')
            dict_out['users'].update(dict({username: temp_dict}))
        result = create_info_tuple(dict_out)
    return result


def task_get_info(task):
    """
    Function for get SRX version
    Output - list of object, present JUN device
    """
    logger = logging.getLogger(__name__)
    logger.debug('Get JunOS firmware version')
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
            logger.debug(f'Fill JunOS properties {host}')
            task.inventory.hosts[host]['error'] = False
#            with open('output/qtech_show_version.txt','w+') as f:
#                f.write(r.result)
            result.append(parse_info(host, res.result))
    return result


def task_get_users(task):
    """
    Function for get user from JUN
    Output - list of object, present JUN device with users
    """
    logger = logging.getLogger(__name__)
    logger.debug('Get JUNOS users info')
    result = list()
    out = task.run(task=netmiko_send_command,
                   command_string="show configuration system login")
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning('Failed task on device {}'.format(task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = True
    for host, res in out.items():
        if not res.failed:
            logger.debug('Fill JUNOS users properties from device {}'.format(task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = False
#            with open('output/junos_show_conf_system_login.txt','w+') as f:
#                f.write(r.result)
            result.append(parse_users(host, res.result))
    return result


def task_create_user(task: Task, username, password, userclass='super-user', crypt_m=crypt.METHOD_MD5):
    """
    Function for create user, default class super-user
    Output - dict {'complete':[], 'fail':[]}
    """
    logger = logging.getLogger(__name__)
    logger.debug('Create user')
    hash_password = crypt.crypt(password, crypt_m)
    config_commands = ['set system login user {} class {}'.format(username, userclass),
                       'set system login user {} authentication encrypted-password {}'.format(username, hash_password)]
    logger.debug(config_commands)
    result = {'completed': [], 'failed': []}
    out = task.run(task=netmiko_send_config, config_commands=config_commands)
    print_result(out)
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning(f'Failed task on device {host}')
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


def task_commit(task):
    """
    Function for commit config for JUN
    Output - {'complete':[],'failed':[]}
    """
    logger = logging.getLogger(__name__)
    logger.debug('Run commit for JUNOS')
    result = {'completed': [], 'failed': []}
    out = task.run(task=netmiko_commit, and_quit=True, delay_factor=4)
    print_result(out)
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning('Failed task on device {}'.format(task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = True
    for host, res in out.items():
        if not res.failed:
            logger.debug('Commit on device {}'.format(task.inventory.hosts[host].name))
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
