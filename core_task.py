'''
Core module for general task and functions
'''
import os
import logging
import tempfile
import shutil
import hashlib
import zipfile
import yaml

from time import gmtime, strftime
from collections import namedtuple
import paramiko
from ansible_vault import Vault
from scp import SCPClient
from nornir_napalm.plugins.tasks import napalm_get

from ansible_vault import Vault
from ansible.constants import DEFAULT_VAULT_ID_MATCH
from ansible.parsing.vault import VaultLib
from ansible.parsing.vault import VaultSecret

#class DeviceData:
#    '''
#    Device Data class for data saving
#    '''
#
#    def __init__(self, **kwargs):
#        for key, value in kwargs.items():
#            setattr(self, key, value)

def get_filehash_md5_bin(filename):
    '''
    function calc md5 sum for all files (binary or plain)
    '''
    buf_size = 4096
    md5 = hashlib.md5()
    with open(filename, 'rb') as process_file:
        while True:
            data = process_file.read(buf_size)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()

def unzip_file(zipfile_path, extract_dir='./'):
    '''
    Function for unpack zip archive
    '''
    result = False
    logger = logging.getLogger(__name__)
    if not os.path.isdir(extract_dir):
        logger.info(f'Creating dir {extract_dir}')
        os.mkdir(extract_dir)
    logger.info(f'Extract files from {zipfile_path} to {extract_dir}')
    with zipfile.ZipFile(zipfile_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
        result = True
    return result


def create_info_tuple(info_dict):
    '''
    function create namedtuple from dict for easy access to properties
    '''
    result = None
    # create namedtuple class
    general_namedtuple = namedtuple('info', info_dict.keys())
    # fill namedtuple class value from info_dict
    result = general_namedtuple(*info_dict.values())
    return result

def summary_devices_descr(devices_list_p1, devices_list_p2, shared_attr='hostname'):
    '''
    Function for summary 2 lists of namedtuple with shared fields
    Device compare for fields - name
    Result list contains with namedtuple with all keys in original list member, default = None
    '''
    result = list()
    # Calc summary keys from 2 type of namedtuples
    summary_keys = [key for device in devices_list_p1+devices_list_p2 for key in device._fields]
    # Fill null dict
    null_dict = {key:'None' for key in set(summary_keys)}
    # Cycle for list with p1 properties
    for device in devices_list_p1:
        # Init result dict
        device_summary = dict()
        # Update with null_dict
        device_summary.update(null_dict)
        # Upadate with dict as namedtuple from list_p1
        device_summary.update(device._asdict())
        # Find all device with equal shared_attr in list_p2
        devices_p2_sel_device = [x for x in devices_list_p2 if getattr(x, shared_attr) == getattr(device, shared_attr)]
        # Update dict with all equal device
        for device_p2 in devices_p2_sel_device:
            device_summary.update(device_p2._asdict())
        tn_summary = namedtuple('summary', device_summary.keys(), defaults=(None,))
        # Create namedtuple tn_summary and append to result
        result.append(tn_summary(*device_summary.values()))
    return result

def read_vault(vaultfile,passwordfile):
    with open(passwordfile, "rb") as file_pass:
        password = file_pass.readline().strip()
        vault = VaultLib([(DEFAULT_VAULT_ID_MATCH, VaultSecret(password))])
        decrypt_text_binary = vault.decrypt(open(vaultfile).read())
        decrypt_text = decrypt_text_binary.decode('utf-8')
        return yaml.safe_load(decrypt_text) 

def init_creds(task, vault, passwordfile):
    '''
    Set creds in nornir inventory object
    '''
    groups_cred = read_vault(vault, passwordfile)
    for key, group in task.inventory.groups.items():
        group.username = groups_cred[key]['username']
        group.password = groups_cred[key]['password']
#        logger.debug('Group {} username {}'.format(key, groups_cred[key]['username']))
#        logger.debug('Group {} password {}'.format(key, groups_cred[key]['password']))


def task_get_napalm_config(task, mode, output_dir):
    '''
    Get device configuration with napalm plugin
    '''
    logger = logging.getLogger(__name__)
    logger.debug('Get startup config from devices (napalm)')
    out = task.run(napalm_get, getters=['get_config'])
    if out.failed:
        for host in out.failed_hosts.keys():
            logger.warning(f"Device {host} config not local save")
            task.inventory.hosts[host]['error'] = True
    else:
        for host, res in out.items():
            if not res.failed:
                device_config_file = output_dir+'//'+host+'_' + \
                    strftime("%Y-%m-%d_%H%M%S", gmtime())+'.cfg'
                logger.debug(
                    f'Save config {host} to file {device_config_file}')
                with open(device_config_file, 'w') as file:
                    file.write(res.result['get_config'][mode])


def scp_get_file(host, src, dst, user, password):
    '''
    Get file from device throw scp
    '''
    logger = logging.getLogger(__name__)
    logger.debug('Get file {} from device {}'.format(src, host))
    logger.debug('Create ssh connect to device {}'.format(host))
    ssh = create_sshclient(host, 22, user, password)
    scp = SCPClient(ssh.get_transport())
    logger.debug('Generate tmp file')
    temp_file = tempfile.NamedTemporaryFile()
    logger.debug("Get file {} to {}".format(src, temp_file.name))
    try:
        scp.get(src, temp_file.name)
        logger.debug("Copy file {} to {}".format(temp_file.name, dst))
        shutil.copyfile(temp_file.name, dst)
    except:
        logger.error('Error copy {} on device {}'.format(host, src))
    finally:
        scp.close()
        ssh.close()
        temp_file.close()

def scp_put_file(host, src, dst, user, password):
    '''
    Put file from device throw scp
    '''
    logger = logging.getLogger(__name__)
#    logger.debug('Put file {} to device {}'.format(src, host))
#    logger.debug('Create ssh connect to device {}'.format(host))
    ssh = create_sshclient(host, 22, user, password)
    scp = SCPClient(ssh.get_transport())
    logger.debug("Put file {} to {}".format(src, dst))
    try:
        scp.put(src, dst)
        logger.debug("Copy file {} to {} - OK".format(src, dst))
    except:
        logger.error('Error copy {} on device {}'.format(host, src))
    finally:
        scp.close()
        ssh.close()

def create_sshclient(server, port, user, password):
    '''
    Create general ssh client connection
    '''
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

def sum_size_files(filepath_list):
    '''
    Calc size for list filespath
    '''
    filesize_list = [os.path.getsize(filepath) for filepath in filepath_list]
    return sum(filesize_list)


def main():
    '''
    Main
    '''
    logger = logging.getLogger(__name__)
    logger.info('Start script')
    logger.info('End script')


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


configure_logging()
if __name__ == "__main__":
    main()
