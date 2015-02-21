# coding=big5
import os
import sys


def text_to_win_big5(text):
    text = text.replace('\r\n', '\n')
    text = text.replace('\r', '\n')
    if type(text) is unicode:
        text = text.encode('big5')
    return text


def parse(text):
    big5str = []
    i = 0
    while i < len(text):
        if '\x81' <= text[i] <= '\xfe':
            big5str += [text[i:i+2]]
            # print(text[i:i+2].decode('big5'), end='')
            i += 2
        else:
            big5str += [text[i]]
            # print(text[i], end='')
            i += 1
    return big5str


def pyinstaller_resource_path(path):
    return os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else '', path)

shop_path = pyinstaller_resource_path('shop')
data_path = pyinstaller_resource_path('data')