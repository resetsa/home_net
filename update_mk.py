# -*- coding: utf-8 -*-
'''
Module for update routeros devices
'''

import os
import logging

from nornir import InitNornir
from nornir.core.filter import F
import core_routeros_task
import core_task

VAULT = 'inventory/creds.yaml'
PASSWORDVAULT = 'private/vault.passwd'
CHECKSUM_URL = 'https://mikrotik.com/download'
VERSION = '6.47.7'
PACKAGES_DIR = 'routeros_package'
FREE_MEMORY_LIMIT = 50*1024*1024


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
    logger.info("Start program for update RouterOS devices")

    logger.debug("Init nornir enviroment")
    all_devices = InitNornir(config_file="config.yaml")

    # Set auth information
    logger.debug('Fill access info from vault {}'.format(VAULT))
    core_task.init_creds(all_devices, VAULT, PASSWORDVAULT)

    logger.debug("Run task for get os version")
    routeros_info = core_routeros_task.task_get_info(
        all_devices.filter(F(groups__contains="routeros")))

    logger.debug("Run task for get packages on devices")
    routeros_packages = core_routeros_task.task_get_packages(
        all_devices.filter(F(groups__contains="routeros")))

    device_summary = core_task.summary_devices_descr(routeros_info, routeros_packages)
    logger.info('Start precheck for updating')
    file_md5_map = core_routeros_task.get_checksum(CHECKSUM_URL, VERSION)
    for device in device_summary:
        logger.warning(f'Check device {device.hostname} for need update')
        if device.version != VERSION:
            logger.info(f'Device {device.hostname} version {device.version} - need update to {VERSION}')
            packages_file = core_routeros_task.download_packages(VERSION, device.arch,
                                                                 download_dir=PACKAGES_DIR,
                                                                 hash_dict=file_md5_map)
            if packages_file:
                core_task.unzip_file(packages_file, PACKAGES_DIR)
            logger.debug(f'Build list package for transfer to device {device.hostname}')
            update_file_list = core_routeros_task.build_update_filelist(device, VERSION, PACKAGES_DIR)
            size_files = core_task.sum_size_files(update_file_list)
            logger.info(f'Device {device.hostname} need {size_files/(1024*1024)} Mb')
            # TODO Do with nornir.plugins.tasks.files.sftp
            logger.debug(f'Free memory {device.freememory}Mb. Check memory size for upload files')
            if float(device.freememory)*1024*1024 - size_files > FREE_MEMORY_LIMIT:
                logger.debug(f'Device {device.hostname} have enough memory for upload packages')
                logger.info(f'Update device {device.hostname}')
                for update_file in update_file_list:
                    dst_file = os.path.basename(update_file)
                    core_task.scp_put_file(device.address, update_file, dst_file,
                                           all_devices.inventory.hosts[device.hostname].username,
                                           all_devices.inventory.hosts[device.hostname].password)
            else:
                logger.error(f'Device {device.hostname} not have free memory for upload update packages')
    logger.info("End program for update. Please reboot devices manual")

configure_logging()
if __name__ == "__main__":
    main()
