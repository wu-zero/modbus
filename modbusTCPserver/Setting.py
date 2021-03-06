import time
from copy import deepcopy

import xlrd
import xlwt

import utils.Convert as Convert


SYS_ANALOG_INPUTS_BLOCK_ADDRESS = 4000 -1
SYS_HOLDING_REGISTERS_BLOCK_ADDRESS = 5000 -1

# ===========================系统参数协议=========================
Sys_Parameter_Address = 4000 - 1
# sensors_id  sensors_name sensors_address
System_Parameter = [
    'version_num',
    'station_num',
    'sensor_num',
    'time_stamp']
System_Parameter_Config = {
    'version_num': [0, 'uint16', 1],
    'station_num': [1, 'uint16', 0],
    'sensor_num':  [2, 'uint16', 5],
    'time_stamp':  [3, 'uint32', int(time.time())],
    'reserve':     [5, 'unknow', 0]
}
# ============================树莓派系统参数设置协议================
Pi_Time_stamp_Address = 5000 - 1
Extern_Zigbee_Address_Address = 5002 - 1
# Hidden_Address = 6000 - 1


# ============================传感器模块协议=======================
SENSOR_MODULE_NUM = 5
Sensor_Module_Id_List = [1, 2, 3, 4, 5]
Sensor_Module_Address_Dict = {1: 4021 - 1, 2: 4051 - 1, 3: 4081 - 1, 4: 4111 - 1, 5: 4141 - 1}
Sensor_Module_InstallNum_Dict = {1: 'YTHA-1', 2: 'YTHA-2', 3: 'YTHA-3', 4: 'YTHA-4', 5: 'YTHA-5'}
try:
    data = xlrd.open_workbook('../doc/setting.xls')
    table = data.sheets()[0]  # 打开第一张表
    nrows = 5     # 获取表的行数
    for i in range(SENSOR_MODULE_NUM+1):   # 循环逐行打印
        if i == 0:  # 跳过第一行
            continue
        Sensor_Module_InstallNum_Dict[int(i)] = table.row_values(i)[1]
except Exception as err:
    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet('sheet1', cell_overwrite_ok=True)
    worksheet.write(0, 0, label='Sensor_ModuleId_Id')
    worksheet.write(0, 1, label='Install_Num')
    for i in range(SENSOR_MODULE_NUM+1):
        if i == 0:  # 跳过第一行
            continue
        worksheet.write(i, 0, label=int(i))
        worksheet.write(i, 1, label=Sensor_Module_InstallNum_Dict[int(i)])
    workbook.save('../doc/setting.xls')

Sensor_Module = [
    'module_id',
    'install_num',
    'time_stamp',
    'temperature',
    'humidity',
    'co2',
    'pm2.5',
    'pm10',
    'short_address',
    'reserve']
#     name  address+  type   初始值
Sensor_Module_Config = {
    'module_id':     [0, 'uint16',   1],
    'install_num':   [1, 'char*10',  'YTHA-7'],
    'time_stamp':    [6, 'uint32',   0],
    'temperature':   [8, 'float',    0.0],
    'humidity':      [10, 'float',   0.0],
    'co2':           [12, 'float',   0.0],
    'pm2.5':         [14, 'float',   0.0],
    'pm10':          [16, 'float',   0.0],
    'short_address': [18, 'uint16',  123],
    'reserve':       [19, 'unknow',  0]
}


# ============================ZigBee串口==========================
SERIAL_ADDRESS = '/dev/ttyS0'  # '/dev/ttyS0'

# 获取串口地址
def get_serial_address():
    return SERIAL_ADDRESS


# 获取传感器模块地址
def get_module_address_from_id(module_id):
    if module_id in Sensor_Module_Id_List:
        address_begin = Sensor_Module_Address_Dict[module_id] + Sensor_Module_Config['time_stamp'][0]
        return address_begin
    else:
        return None


# def get_values_from_bytes(bytes_data):
#     values = []
#     Convert.convert_to_uint16_data(values, 'bytes', bytes_data)
#     return values


def get_time_bytes():
    time_data = int(time.time())
    result = time_data.to_bytes(4, byteorder='little')
    return result


#  ===================modbus初始化(从当前程序获得数据）==========================================
def get_system_parameter_address_and_values():
    address_begin = Sys_Parameter_Address
    values = []
    for i in System_Parameter:
        values = Convert.convert_to_uint16_data(System_Parameter_Config[i][1], System_Parameter_Config[i][2], values)
    return address_begin, values


def get_sensor_address_and_values(module_id):
    if module_id in Sensor_Module_Id_List:
        address_begin = Sensor_Module_Address_Dict[module_id]

        sensor_config = deepcopy(Sensor_Module_Config)
        sensor_config['module_id'][2] = module_id
        sensor_config['install_num'][2] = Sensor_Module_InstallNum_Dict[module_id]
        values = []
        for i in Sensor_Module:
            values = Convert.convert_to_uint16_data(sensor_config[i][1], sensor_config[i][2], values)
        return address_begin, values
    else:
        pass


#  ===================modbus更新时间(从系统时间获得数据)=====================================================
def get_timestamp_address_and_values():
    address_begin = Sys_Parameter_Address + System_Parameter_Config['time_stamp'][0]
    values = Convert.convert_to_uint16_data(System_Parameter_Config['time_stamp'][1], int(time.time()))
    return address_begin, values


def get_Pi_timestamp_address_and_values():
    address_begin = Pi_Time_stamp_Address
    values = Convert.convert_to_uint16_data('uint32', int(time.time()))
    return address_begin, values


#  ====================解析zigbee数据(数据类型bytes,小端模式)==================================================
#  zigbee数据->modbus数据
def get_address_and_values_from_bytes(bytes_data):
    data_module_num = bytes_data[:2]
    data_others = bytes_data[2:]

    # 获得地址起始值
    sensor_module_num = Convert.byte2_to_uint16(data_module_num)
    address_begin = get_module_address_from_id(sensor_module_num)

    values = Convert.convert_to_uint16_data('bytes', data_others)
    return address_begin, values


#  zigbee数据->真实数据
def get_module_id_and_timestamp_from_bytes(bytes_data):
    data_module_num = bytes_data[:2]
    data_others = bytes_data[2:]

    # 获得传感器模块号
    sensor_module_id = Convert.byte2_to_uint16(data_module_num)
    # 获得时间戳数值
    time_stamp = []
    Convert.convert_to_real_data(time_stamp, Sensor_Module_Config['time_stamp'][1],
                                 data_others[(Sensor_Module_Config['time_stamp'][0] - 6) * 2:])
    time_stamp = time_stamp[0]
    return sensor_module_id, time_stamp


'''
def get_real_data(bytes_data):
    data_module_id = bytes_data[:2]

    data_others = bytes_data[2:]
    values = []
    # 添加module_num
    Convert.convert_to_real_data(values, Sensor_Module_Config['module_id'][1], data_module_id)
    # 添加数据
    for sensor_module_part in Sensor_Module[2:]:
        Convert.convert_to_real_data(values, Sensor_Module_Config[sensor_module_part][1], data_others[(Sensor_Module_Config[sensor_module_part][0] - 6) * 2:])
    return values
'''


#  ===================解析modbus request命令(数据类型bytes,大端模式转化为uint16，小端模式)============================
def solve_multiple_request(bytes_data):
    address = Convert.byte2_to_uint16(bytes_data[1:3], little_endian=False)
    values = Convert.bytes_to_uint16(bytes_data[6:], little_endian=False)
    return address, values


def solve_single_request(bytes_data):
    address = Convert.byte2_to_uint16(bytes_data[1:3], little_endian=False)
    values = Convert.bytes_to_uint16(bytes_data[3:], little_endian=False)
    return address, values


if __name__ == '__main__':
    # print(get_real_data(b'\0\0cdefglskjdfdsddddewwwwwwwwww\r\n'))
    # pass
    # a = get_time_bytes()
    # print(a)
    # for i in range(len(a)):
    #     print(a[i])
    a = get_module_id_and_timestamp_from_bytes(b'\x04\x00p\xed\xd3B\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd2\xdb\xdf[')
    print(a)
    print(Sensor_Module_InstallNum_Dict)
    print(get_timestamp_address_and_values())
