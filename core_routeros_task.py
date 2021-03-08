'''
Module tasks and functions for RouterOS devices
'''

import logging
import os
import sys
assert sys.version_info.major == 3, 'For script run please use python3'
import re
from time import gmtime, strftime
import datetime
import textfsm
import requests

from bs4 import BeautifulSoup
from core_task import scp_get_file
from core_task import create_info_tuple
from core_task import get_filehash_md5_bin

from nornir_netmiko.tasks import netmiko_send_command
from nornir_utils.plugins.functions import print_result
from nornir_netmiko.tasks import netmiko_send_config
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

def get_checksum(url, version):
    '''
    Function for parse download page
    Return empty dict or dict with filename:hash
    '''
    result = dict()
    # regex for match string
    # example string, routeros-6.46.6-npk: e1a895225d4292ede73bc01a4cbcc8e6
    regex = r".*-\d\.\d+\.\d+\.\w{3}: [a-f0-9]{32}$"
    logger = logging.getLogger(__name__)
    logger.debug(f'Try access to URL {url}')
    web_req = requests.get(url)
    logger.debug('HTTP code {}'.format(web_req.status_code))
    if web_req.status_code == 200:
        logger.debug('Load HTML context')
        html_text = web_req.content
        soap = BeautifulSoup(html_text, "html.parser")
        logger.debug(f"Get HTML block with id=md5_{version.replace('.','_')}'")
        block_md5 = soap.find(id=f"md5_{version.replace('.','_')}")
        md5_list = block_md5.find_all(string=re.compile(regex))
        result = {md5_file.split(':')[0].strip():md5_file.split(':')[1].strip() for md5_file in md5_list}
    return result

def download_packages(version, arch, download_dir='./routeros_package', hash_dict=None):
    '''
    Function to download and unzip packages from internet
    '''
    result = False
    need_download = True
    logger = logging.getLogger(__name__)
    url = f'https://download.mikrotik.com/routeros/{version}/all_packages-{arch}-{version}.zip'
    logger.debug(f'Check {download_dir} exists')
    if not os.path.isdir(download_dir):
        logger.info(f'Creating dir {download_dir}')
        os.mkdir(download_dir)
    dest_file = url.split('/')[-1]
    dest_full_path = os.path.join(download_dir, dest_file)
    logger.debug(f'Check file exist {dest_full_path}')
    if os.path.isfile(dest_full_path):
        logger.info(f'File {dest_full_path} exist, verify md5 sum')
        if get_filehash_md5_bin(dest_full_path) != hash_dict.get(dest_file):
            logger.info('Hash is not equal. File will be donwload')
            need_download = True
        else:
            logger.info('Hash is equal. Skipping download')
            need_download = False
    if need_download:
        logger.debug(f'Path for download {dest_full_path}')
        logger.info(f'Send request {url}')
        web_req = requests.get(url)
        logger.debug('HTTP code {}'.format(web_req.status_code))
        if web_req.status_code == 200:
            logger.debug(f'Save to file {dest_full_path}')
            with open(dest_full_path, 'wb') as package_file:
                package_file.write(web_req.content)
        result = dest_full_path
    return result

def parse_info(hostname, address, dict_prop):
    '''
    Create object from hostname, dict_prop
    '''
    template_file_path = 'templates/routeros_system_resource_print.template'
    result = None
    with open(template_file_path) as template:
        fsm = textfsm.TextFSM(template)
#        print(fsm.header)
#        print(fsm.ParseText(out)[0])
        dict_out = dict(zip(fsm.header, fsm.ParseText(dict_prop)[0]))
        dict_out['hostname'] = hostname
        dict_out['address'] = address
#        result = DeviceData(**dict_out)
        result = create_info_tuple(dict_out)
    return result


def parse_routerboard(hostname, address, dict_prop):
    '''
    Create object from routerboard output
    '''
    template_file_path = 'templates/routeros_system_routerboard.template' 
    result = None
    with open(template_file_path) as template:
        fsm = textfsm.TextFSM(template)
        dict_out = dict(zip(fsm.header, fsm.ParseText(dict_prop)[0]))
        dict_out['hostname'] = hostname
        dict_out['address'] = address
        result = create_info_tuple(dict_out)
    return result


def parse_users(hostname, dict_users):
    '''
    Create object from hostname, dict_users
    '''
    result = None
    dict_out = dict()
    with open('templates/routeros_user_export_verbose.template') as template:
        fsm = textfsm.TextFSM(template)
        dict_out['hostname'] = hostname
        dict_out['users'] = dict()
        for user in fsm.ParseText(dict_users):
            temp_dict = dict(zip(fsm.header, user))
            username = temp_dict.pop('username')
            dict_out['users'].update(dict({username: temp_dict}))
        result = create_info_tuple(dict_out)
    return result

def parse_packages(hostname, dict_props):
    '''
    Create object from hostname, dict_prop
    '''
    result = None
    dict_out = dict()
    with open('templates/routeros_system_package.template') as template:
        fsm = textfsm.TextFSM(template)
        dict_out['hostname'] = hostname
        dict_out['packages'] = dict()
        for package in fsm.ParseText(dict_props):
            temp_dict = dict(zip(fsm.header, package))
            packagename = temp_dict.pop('name')
            dict_out['packages'].update(dict({packagename: temp_dict}))
        result = create_info_tuple(dict_out)
    return result

def task_get_info(task: Task):
    """
    Function for get RouterOS version
    Output - list of object, present RouterOS device
    """
    logger = logging.getLogger(__name__)
    logger.debug('Get RouterOS version')
    result = list()
    out = task.run(task=netmiko_send_command,
                   command_string="system resource print")
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning(f'Failed task on device {host}')
            task.inventory.hosts[host]['error'] = True
    for host, res in out.items():
        if not res.failed:
            logger.debug(f'Fill RouterOS properties {host}')
            task.inventory.hosts[host]['error'] = False
 #           with open('output/debug.txt','w+') as f:
 #               f.write(r.result)
            result.append(parse_info(host, task.inventory.hosts[host].hostname, res.result))
    return result

def task_get_packages(task: Task):
    """
    Function for get RouterOS installed packages
    Output - list of object, present RouterOS device
    """
    logger = logging.getLogger(__name__)
    logger.debug('Get RouterOS installed packages')
    result = list()
    out = task.run(task=netmiko_send_command,
                   command_string="system package print terse")
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning(f'Failed task on device {host}')
            task.inventory.hosts[host]['error'] = True
    for host, res in out.items():
        if not res.failed:
            logger.debug(f'Fill RouterOS properties {host}')
            task.inventory.hosts[host]['error'] = False
#            with open('output/routeros_system_package.txt','w+') as f:
#               f.write(res.result)
            result.append(parse_packages(host, res.result))
    return result

def task_get_routerboard(task: Task):
    """
    Function for get RouterOS firmware version active/upgrade
    Output - list of object, present RouterOS device
    """
    logger = logging.getLogger(__name__)
    logger.debug('Get RouterOS firmware version')
    result = list()
    out = task.run(task=netmiko_send_command,
                   command_string="system routerboard print")
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning(f'Failed task on device {host}')
            task.inventory.hosts[host]['error'] = True
    for host, res in out.items():
        if not res.failed:
            logger.debug(f'Fill RouterOS firmware version {host}')
            task.inventory.hosts[host]['error'] = False
            result.append(parse_routerboard(host, task.inventory.hosts[host].hostname, res.result))
    return result


def task_get_users(task: Task):
    """
    Function for get user from RouterOS
    Output - list of object, present RouterOS device with users
    """
    logger = logging.getLogger(__name__)
    logger.debug('Get RouterOS users info')
    result = list()
    out = task.run(task=netmiko_send_command,
                   command_string="user export verbose compact", use_timing=True, delay_factor=8)
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning('Failed task on device {}'.format(task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = True
    for host, res in out.items():
        if not res.failed:
            logger.debug('Fill RouterOS users properties from device {}'.format(task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = False
#            with open('output/routeros_user_export_verbose_compact.txt','w+') as f:
#                f.write(r.result)
            result.append(parse_users(host, res.result))
    return result


def task_get_bin_config(task: Task, output_dir):
    '''
    Get bin config
    '''
    logger = logging.getLogger(__name__)
    logger.debug('Get binary config from RouterOS devices')
    file_on_device = 'autosave'
    logger.debug(
        'Send command - system backup save dont-encrypt=yes name={}'.format(file_on_device))
    out = task.run(task=netmiko_send_command,
                   command_string='system backup save dont-encrypt=yes name={}'.format(file_on_device))
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning(f"Device {host} config not local export")
            task.inventory.hosts[host]['error'] = True
    else:
        for host, res in out.items():
            if not res.failed:
                device_config_file = output_dir+'//'+host+'_' + \
                    strftime("%Y-%m-%d_%H%M%S", gmtime())+'.backup'
                scp_get_file(task.inventory.hosts[host].hostname, '{}.backup'.format(file_on_device), device_config_file,
                             task.inventory.hosts[host].username, task.inventory.hosts[host].password)


def task_get_export(task: Task, output_dir):
    '''
    Get export compact
    '''
    logger = logging.getLogger(__name__)
    logger.debug('Get export config from RouterOS devices')
    file_on_device = 'autoexport'
    logger.debug(
        'Send command - export compact file={}'.format(file_on_device))
    out = task.run(task=netmiko_send_command, command_string='export compact file={}'.format(file_on_device),
                   use_timing=True, delay_factor=5)
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning(f"Device {host} config not local export")
            task.inventory.hosts[host]['error'] = True
    else:
        for host, res in out.items():
            if not res.failed:
                device_config_file = output_dir+'//'+host+'_' + \
                    strftime("%Y-%m-%d_%H%M%S", gmtime())+'.cfg'
                scp_get_file(task.inventory.hosts[host].hostname, '{}.rsc'.format(file_on_device), device_config_file,
                             task.inventory.hosts[host].username, task.inventory.hosts[host].password)


def task_create_user(task: Task, username, password, group='full'):
    """
    Function for create user, default with group full
    Output - dict {'completed':[], 'failed':[]}
    """
    logger = logging.getLogger(__name__)
    logger.debug('Create user')
    config_command = 'user add name={} group={} password="{}"'.format(
        username, group, password)
    logger.debug(config_command)
    result = {'completed': [], 'failed': []}
    out = task.run(task=netmiko_send_command, command_string=config_command)
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

def task_update_point(task: Task, address, username, password):
    """
    Function for create update points in RouterOS devices
    Output - dict {'completed':[], 'failed':[]}
    """
    logger = logging.getLogger(__name__)
    logger.debug('Create new update point')
    config_commands = [f'system upgrade upgrade-package-source add address={address} user={username}', f'{password}']
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
            logger.debug('Create update point {} with device {} '.format(
                address, task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = False
            result['completed'].append(host)
#            result.append(parse_info(h,r.result))
    return result

def task_schedule_reboot(task: Task, timeout):
    '''
    Function - create task for schedule reboot on RouterOS
    input - timeout value in seconds
    '''
    logger = logging.getLogger(__name__)
    schedule_name = 'System_autoreboot'
    reboot_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
    reboot_time_fs = strftime('%H:%M:%S', reboot_time.timetuple())
    logger.debug('Create reboot schedule')
    config_commands = [f'/system scheduler remove [find name="{schedule_name}"]',
                       f'system scheduler add name={schedule_name} on-event="system reboot" start-time={reboot_time_fs} disabled=no']
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
            logger.info('Create restart task on device {} - OK'.format(task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = False
            result['completed'].append(host)
    return result

def task_update_fw(task):
    '''
    Function - update fw on devices
    '''
    logger = logging.getLogger(__name__)
    logger.debug('Updating device')
    config_commands = ['system routerboard upgrade', 'y']
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
            logger.info('Update fw command on device {} - OK'.format(task.inventory.hosts[host].name))
            task.inventory.hosts[host]['error'] = False
            result['completed'].append(host)
    return result


def build_update_filelist(device, version, download_dir):
    '''
    Generate filepath for need packages
    '''
    result = []
    package_mask = '{}-{}-{}.npk'
    for package in device.packages.keys():
        result.append(os.path.join(download_dir, package_mask.format(package, version, device.arch)))
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
