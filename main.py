# -*- coding: utf-8 -*-
"""Модуль работы с электронным табло"""
import sys
import json
import urllib2
import time
import serial

count = 1


def crc8_hash(arr):
    """Вычисление CRC8"""
    crc_m = [0, 94, 188, 226, 97, 63, 221, 131, 194, 156, 126, 32, 163, 253, 31, 65,
             157, 195, 33, 127, 252, 162, 64, 30, 95, 1, 227, 189, 62, 96, 130, 220,
             35, 125, 159, 193, 66, 28, 254, 160, 225, 191, 93, 3, 128, 222, 60, 98,
             190, 224, 2, 92, 223, 129, 99, 61, 124, 34, 192, 158, 29, 67, 161, 255,
             70, 24, 250, 164, 39, 121, 155, 197, 132, 218, 56, 102, 229, 187, 89, 7,
             219, 133, 103, 57, 186, 228, 6, 88, 25, 71, 165, 251, 120, 38, 196, 154,
             101, 59, 217, 135, 4, 90, 184, 230, 167, 249, 27, 69, 198, 152, 122, 36,
             248, 166, 68, 26, 153, 199, 37, 123, 58, 100, 134, 216, 91, 5, 231, 185,
             140, 210, 48, 110, 237, 179, 81, 15, 78, 16, 242, 172, 47, 113, 147, 205,
             17, 79, 173, 243, 112, 46, 204, 146, 211, 141, 111, 49, 178, 236, 14, 80,
             175, 241, 19, 77, 206, 144, 114, 44, 109, 51, 209, 143, 12, 82, 176, 238,
             50, 108, 142, 208, 83, 13, 239, 177, 240, 174, 76, 18, 145, 207, 45, 115,
             202, 148, 118, 40, 171, 245, 23, 73, 8, 86, 180, 234, 105, 55, 213, 139,
             87, 9, 235, 181, 54, 104, 138, 212, 149, 203, 41, 119, 244, 170, 72, 22,
             233, 183, 85, 11, 136, 214, 52, 106, 43, 117, 151, 201, 74, 20, 246, 168,
             116, 42, 200, 150, 21, 75, 169, 247, 182, 232, 10, 84, 215, 137, 107, 53]
    cid = arr[0]
    for i in range(1, 13):
        cid = crc_m[cid] ^ arr[i]
    return crc_m[cid]


def form_byte_array(idx, val, com_count, blnconf, blcount, blspeed):
    """Формируем байтовый массив"""
    result = [0x10]
    arr = [0xb9]
    t_id = [idx]
    arr.extend(t_id)
    arr.extend([0, 0, 0])
    for t_c in val:
        arr.extend([int(t_c)])
    arr.extend([2, com_count, blnconf, blcount, blspeed])
    hash_elem = crc8_hash(arr)
    arr.extend([hash_elem])
    end = [0x10, 0xfe]
    arr.extend(end)
    result.extend(arr)
    return result


def write_serial(device, baud_rate, eight_bits, parity, stop_bits, value):
    """Запись в serial устройство"""
    ser = serial.Serial(device, baud_rate, eight_bits, parity, stop_bits)
    if ser.isOpen():
        ser.flushInput()
        ser.flushOutput()
        ser.write(bytearray(value))
    else:
        print 'Cannot open', device


def open_settings(filename):
    """Открывает файл настроек в формате JSON и возвращает объект настроек"""
    result = None
    with open(filename, 'r') as settings:
        result = json.load(settings)
    return result


def make_uri(uri, context, endpoint):
    """Готовит URI для запроса"""
    return uri + context + endpoint


def http_request(uri, resource):
    """Запрос по URI с ресурсом"""
    try:
        return urllib2.urlopen(uri + '?resourceGroupId=' + str(resource)).read()
    except urllib2.URLError as error:
        print error


def filter_ticket(value):
    """Фильтр вызванных талонов"""
    for item in value:
        for attr, val in item.items():
            if attr == 'tickets':
                for tick in val:
                    for tick_attr, tick_val in tick.items():
                        if tick_attr == 'state' and tick_val == 2:
                            return value


def ticket_parse(res):
    """Парсим полученные талоны из http-ответа"""
    for attr, val in json.loads(res).items():
        if attr == 'tickets' and val:
            return filter_ticket(val)


def boards_parse(uri, boards):
    """Парсим табло настроек и получаем талоны"""
    response = None
    result = []
    for board in boards:
        for board_setting, value in board.items():
            if board_setting == 'resources':
                for resource in value:
                    response = http_request(uri, resource)
                    if response and ticket_parse(response):
                        result.extend(ticket_parse(response))
    filtered_tickets_parse(result, boards)
    global count
    if count == 1:
        count = 2
    else:
        count = 1


def boards_filter(boards, resource):
    """Фильтр табло"""
    result = []
    for board in boards:
        for attr, val in board.items():
            if attr == 'resources' and resource in val:
                result.extend([board])
    return result


def filtered_tickets_parse(tickets, boards):
    """Парсинг отфильтрованных талонов и вызвов на табло"""
    for ticket in tickets:
        for tick in ticket['tickets']:
            if tick['state'] == 2:
                write_to_board(boards, tick['name']
                               [-3:], ticket['resourceGroupId'])


def write_to_board(boards, value, resource):
    """Отправка на табло"""
    filtered = boards_filter(boards, resource)[0]
    idx = filtered['id']
    blnconf = filtered['blnconf']
    blcount = filtered['blcount']
    blspeed = filtered['blspeed']
    device = filtered['serial']
    byte_array = form_byte_array(idx, value, count, blnconf, blcount, blspeed)
    write_serial(device, 9600, serial.EIGHTBITS,
                 serial.PARITY_NONE, serial.STOPBITS_ONE, byte_array)


def main():
    """Main"""
    settings = open_settings(sys.argv[1])
    uri = ''
    context = None
    endpoint = None
    freq = None
    boards = []
    for setting, value in settings.items():
        if setting == 'boards':
            boards.extend(value)
        elif setting == 'frequency':
            freq = value
        elif setting == 'restHost':
            uri = value
        elif setting == 'restContext':
            context = value
        elif setting == 'restQuery':
            endpoint = value
    uri = make_uri(uri, context, endpoint)
    while True:
        boards_parse(uri, boards)
        time.sleep(freq // 1000)


if __name__ == "__main__":
    main()
