'''
Module for testing get creds from vault
'''

import os
import argparse
import logging
import sys
from core_task import read_vault

assert sys.version_info.major == 3, 'For script run please use python3'


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

    logger.debug("Parse arguments")
    parser = argparse.ArgumentParser(
        description='Get credential from ansible vault file')
    parser.add_argument('--vault', action='store',
                        required=True, help="Vault filename")
    parser.add_argument('--passfile', action='store',
                        required=True, help="Password file")
    args = parser.parse_args()

    logger.debug("Vault file: {}".format(args.vault))
    logger.debug("Password file: {}".format(args.passfile))

    out = read_vault(args.vault, args.passfile)
    [print(k,out[k]) for k in out.keys()]

    logger.info("End program")


configure_logging()
if __name__ == "__main__":
    main()
