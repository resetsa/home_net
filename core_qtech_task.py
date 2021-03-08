'''
Module tasks and functions for Qtech devices
'''
import logging
import sys
assert sys.version_info.major == 3, 'For script run please use python3'
import textfsm
from core_task import create_info_tuple
from time import gmtime, strftime


from nornir_netmiko.tasks import netmiko_send_command
from nornir_utils.plugins.functions import print_result
from nornir_netmiko.tasks import netmiko_send_config
from nornir_netmiko.tasks import netmiko_save_config
from nornir.core.task import Task




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
    Create object from hostname, dict_prop
    '''
    result = None
    with open('templates/qtech_show_version.template') as template:
        fsm = textfsm.TextFSM(template)
        dict_out = dict(zip(fsm.header, fsm.ParseText(dict_prop)[0]))
        dict_out['hostname'] = hostname
#        result = DeviceData(**dict_out)
        result = create_info_tuple(dict_out)
    return result


def parse_users(hostname, dict_users):
    '''
    Create object from hostname, users dict
    '''
    result = None
    dict_out = dict()
    with open('templates/qtech_show_startup_include_username.template') as template:
        fsm = textfsm.TextFSM(template)
        dict_out['hostname'] = hostname
        dict_out['users'] = dict()
        for user in fsm.ParseText(dict_users):
            temp_dict = dict(zip(fsm.header, user))
            username = temp_dict.pop('username')
            dict_out['users'].update(dict({username: temp_dict}))
        result = create_info_tuple(dict_out)
    return result


def task_get_info(task: Task):
    """
    Function for get Qtech firmware version
    Output - list of object, present QTech device
    """
    logger = logging.getLogger(__name__)
    logger.debug('Get Qtech firmware version')
    result = list()
    out = task.run(task=netmiko_send_command, command_string="show version")
#    print_result(out)
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning('Failed task on device {}'.format(
                task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = True
    for host, res in out.items():
        if not res.failed:
            logger.debug('Fill QTech firmware properties {}'.format(
                task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = False
#            with open('output/qtech_show_version.txt','w+') as f:
#                f.write(r.result)
            result.append(parse_info(host, res.result))
    return result


def task_get_users(task: Task, configmode='startup'):
    """
    Function for get user from Qtech
    Output - list of object, present Qtech device with users
    """
    logger = logging.getLogger(__name__)
    logger.debug('Get Qtech users info')
    result = list()
    out = task.run(task=netmiko_send_command,
                   command_string="show {} | include username".format(configmode))
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning('Failed task on device {}'.format(
                task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = True
    for host, res in out.items():
        if not res.failed:
            logger.debug('Fill Qtech users properties from device {}'.format(
                task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = False
#            with open('output/qtech_user_export_verbose_compact.txt','w+') as f:
#                f.write(r.result)
            result.append(parse_users(host, res.result))
    return result


def task_create_user(task: Task, username, password, priv=15):
    """
    Function for create user, default with 15 priviledges
    Output - dict {'completed':[], 'fail':[]}
    """
    logger = logging.getLogger(__name__)
    logger.debug('Create user')
    config_commands = ["username {} privilege {} password 0 {}".format(
        username, priv, password)]
    logger.debug(config_commands)
    result = {'completed': [], 'failed': []}
    out = task.run(task=netmiko_send_config, config_commands=config_commands, config_mode_command='config')
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
    out = task.run(task=netmiko_save_config, cmd='write running',
                   confirm=True, confirm_response="y")
    print_result(out)
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning('Failed task on device {}'.format(
                task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = True
    for host, res in out.items():
        if not res.failed:
            logger.debug('Save config on device {}'.format(
                task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = False
            result['completed'].append(host)
    return result

def task_get_config(task: Task, output_dir):
    '''
    Get startup compact
    '''
    SHOW_RUN_COMMAND = 'show run'
    logger = logging.getLogger(__name__)
    logger.debug('Get startup config from Qtech devices')
    logger.debug('Send command - {}'.format(SHOW_RUN_COMMAND))
    out = task.run(task=netmiko_send_command, command_string=SHOW_RUN_COMMAND,use_timing=True, delay_factor=5)
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning(f"Device {host} config not local export")
            task.inventory.hosts[host]['error'] = True
    else:
        for host, res in out.items():
            if not res.failed:
                device_config_file = output_dir+'//'+host+'_' + strftime("%Y-%m-%d_%H%M%S", gmtime())+'.cfg'
                logger.debug('Save config on device {}'.format(task.inventory.hosts[host].name))
                with open(device_config_file,'w') as config_file:
                    config_file.writelines(res.result)

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
