Скрипты автоматизации домашней сети.
===================================

### Используемые модули:
* nornir - 3.0
* [GitHub Pages] (https://github.com/networktocode/ntc-templates)

### В процессе разработки. Только для личного использования, для работы в пром. сети не готово.
------------

#### Инструкция по запуску и применению:

dev_connect.py - получение информации о версия ПО.
```
sas@DESKTOP-2LKG506:~/home-net$ python3 dev_connect.py
2020-08-13 22:06:53,439 - dev_connect - main - INFO - Start program for config network
2020-08-13 22:06:53,439 - dev_connect - main - DEBUG - Init nornir enviroment
2020-08-13 22:06:53,494 - dev_connect - main - DEBUG - Fill access info from vault /home/sas/home-net/inventory/creds.yaml
2020-08-13 22:06:53,564 - dev_connect - main - DEBUG - Run task for get os version
2020-08-13 22:06:53,567 - core_routeros_task - task_get_info - DEBUG - Get RouterOS version
2020-08-13 22:06:59,041 - core_routeros_task - task_get_info - DEBUG - Fill RouterOS properties sw-core
2020-08-13 22:06:59,049 - core_routeros_task - task_get_info - DEBUG - Fill RouterOS properties rt-ext
2020-08-13 22:06:59,053 - core_routeros_task - task_get_info - DEBUG - Fill RouterOS properties rt-vm
2020-08-13 22:06:59,056 - core_routeros_task - task_get_info - DEBUG - Fill RouterOS properties rt-z-01
2020-08-13 22:06:59,059 - core_routeros_task - task_get_info - DEBUG - Fill RouterOS properties rt-con-01
2020-08-13 22:06:59,062 - core_routeros_task - task_get_info - DEBUG - Fill RouterOS properties rt-core-02
2020-08-13 22:06:59,065 - core_qtech_task - task_get_info - DEBUG - Get Qtech firmware version
2020-08-13 22:07:18,058 - core_qtech_task - task_get_info - DEBUG - Fill QTech firmware properties sw-qtech
2020-08-13 22:07:18,065 - core_ios_task - task_get_info - DEBUG - Get IOS version
2020-08-13 22:07:23,579 - core_ios_task - task_get_info - DEBUG - Fill IOS properties sw-access
2020-08-13 22:07:23,580 - core_jun_task - task_get_info - DEBUG - Get JunOS firmware version
2020-08-13 22:07:32,532 - core_jun_task - task_get_info - DEBUG - Fill JunOS properties jun-srx100
2020-08-13 22:07:32,532 - dev_connect - main - INFO - End program for config network
Hostname is sw-core      ROS     6.47.1
Hostname is rt-ext       ROS     6.47.1
Hostname is rt-vm        ROS     6.47.1
Hostname is rt-z-01      ROS     6.47.1
Hostname is rt-con-01    ROS     6.47.1
Hostname is rt-core-02   ROS     6.47.1
Hostname is sw-qtech     Qtech   1.1.5.8(Build245.117)
Hostname is sw-access    IOS     15.1(4)M8
Hostname is jun-srx100   JunOS   12.1X46-D86
```
