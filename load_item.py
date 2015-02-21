#coding=big5
import codecs
from Tkinter import Tk

from Frame import Frame
from Item import Item
import utils


with codecs.open('Data\\test_items-b5.txt', encoding='big5') as textFile:
    text = textFile.read()
itemStr = utils.text_to_win_big5(text).split('\n\n')
item_list = [Item(item_text.strip()) for item_text in itemStr]

root = Frame(None, "首頁")
for item in item_list:
    category = root[item.category][item.type]
    if not category.item_exist(item):
        num = len(root[item.category][item.type].child) + 1
        # Covert half-width num character to full-width for searching simplicity
        fullWidthNum = unichr(0xFEE0 + ord(str(num))).encode('big5').rjust(4)
        root[item.category][item.type][fullWidthNum].item = item

root.build()
r = Tk()
r.withdraw()
r.clipboard_clear()
imgstr = root.get_all_img_str()
r.clipboard_append(imgstr.decode('big5'))




#
# recent_value = pyperclip.paste()
# while True:
#     tmp_value = pyperclip.paste()
#     if tmp_value != recent_value:
#         recent_value = tmp_value
#         if re.match(pattern, recent_value) is not None:
#             print re.match(pattern, recent_value)
#             item_list.append(Item(recent_value))
#         else:
#             break
#     time.sleep(0.3)