'''
Module for test textfsm pattern
'''

import textfsm
from collections import namedtuple

TEXT = '''
    uptime: 8h42m20s
    version: 6.46.5 (stable)
    build-time: Apr/07/2020 08:28:27
    factory-software: 6.43.10
    free-memory: 207.7MiB
    total-memory: 256.0MiB
    cpu: MIPS 1004Kc V2.15
    cpu-count: 4
    cpu-frequency: 880MHz
    cpu-load: 4%
    free-hdd-space: 6.8MiB
    total-hdd-space: 16.3MiB
    write-sect-since-reboot: 1181
    write-sect-total: 13673
    bad-blocks: 0%
    architecture-name: mmips
    board-name: RBM33G
    platform: MikroTik
'''


class DeviceData:
    '''
    Dataclass, no public methods
    '''
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def parse_qtech_info(inputtext):
    '''
    Test func
    '''
    result = None
    with open('templates/qtech_show_version.template') as template:
        fsm = textfsm.TextFSM(template)
        dict_text = dict(zip(fsm.header, fsm.ParseText(inputtext)[0]))
        qtech_tuple = namedtuple('qtech',dict_text.keys())
        qtech = qtech_tuple(*dict_text.values())
    return qtech


with open('output/qtech_show_version.txt') as source:
    text = source.read()
qtech_info=parse_qtech_info(text)
print(qtech_info)

