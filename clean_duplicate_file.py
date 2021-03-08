'''
Modules for clean duplicate files from directory
'''
import logging
import pathlib
import argparse
import os
import hashlib
import sys
import magic
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


def get_filehash_md5_txt(filename, begin_str):
    '''
    Function for calc md5 hash for files
    If file is PLAIN md5 hash for strings, exclude begin with begin_str
    '''
    result = ''
    logger = logging.getLogger(__name__)
    md5 = hashlib.md5()
    mime = magic.Magic(mime=True)
    if 'plain' in mime.from_file(filename):
        logger.debug('Text file - try calc hash md5 without comment string')
        with open(filename, 'r',) as f:
            while True:
                data = f.readline()
                if not data:
                    break
                if not data.startswith(begin_str):
                    md5.update(data.encode('utf-8'))
        result = md5.hexdigest()
    else:
        logger.debug('Binary file - try calc hash md5 as binary data')
        result = get_filehash_md5_bin(filename)
    return result


def get_filehash_md5_bin(filename):
    '''
    function calc md5 sum for all files (binary or plain)
    '''
    buf_size = 4096
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


def delete_duplicate(directory, recursive, delete):
    '''
    function for detect duplicate files in directory
    '''
    logger = logging.getLogger(__name__)
    logger.info('Check files for duplicate in %s', directory)
    md5_hashes = dict()
    if os.path.isdir(directory):
        if recursive:
            f_list = [os.path.join(dp, f) for dp, dn, filenames in os.walk(
                directory) for f in filenames]
        else:
            r, _, f = next(os.walk(directory))
            f_list = [os.path.join(r, fname) for fname in f]
        for file in f_list:
            logger.debug('Processing file %s', file)
            md5_hash = get_filehash_md5_txt(file, '#')
            logger.debug('Add %sto md5_hash', md5_hash)
            if md5_hashes.get(md5_hash):
                logger.info('Duplicate file {} equal with {}'.format(
                    file, md5_hashes[md5_hash]))
                if delete:
                    logger.warning('Delete dupilcate file %s', file)
                    os.unlink(file)
            else:
                md5_hashes[md5_hash] = file
    else:
        logger.error("Directory not exists: %s", directory)


def main():
    '''
    Main
    '''
    logger = logging.getLogger(__name__)
    logger.info("Start program")

    logger.debug("Parse arguments")
    parser = argparse.ArgumentParser(
        description='Clean duplicate from directory')
    parser.add_argument('--folder', '-f', action='store', default=pathlib.Path().absolute(),
                        help="Directory for processing")
    parser.add_argument('--rec', '-r', action='store_true', default=False,
                        help="Select recursive process")
    parser.add_argument('--delete_duplicate', '-d', action='store_true', default=False,
                        help="Only log, without delete duplicate")
    args = parser.parse_args()

    logger.debug("Directory for process: %s", args.folder)
    logger.debug("Recursive: %s", args.rec)
    logger.debug("Delete duplicate: %s", args.delete_duplicate)
    delete_duplicate(args.folder, args.rec, args.delete_duplicate)

    logger.info("End program")


configure_logging()
if __name__ == "__main__":
    main()
