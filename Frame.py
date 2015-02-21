# coding=big5
import codecs
import os
import textwrap

import numpy as np

from Item import Item
import utils



# TODO New Colorize System
class Frame:
    width = 78
    height = 23

    keyNext = "@d"
    keyEnter = "@r"
    keyBack = "@l"
    keyPrev = "@u"
    keyPageUp = '@P'
    keyPageDown = '@N'

    home_template = os.path.join(utils.data_path, 'home_template.ans')
    category_template = os.path.join(utils.data_path, 'category_template.ans')
    item_list_template = os.path.join(utils.data_path, 'item_list_template.ans')

    class Option:
        def __init__(self, key='', cmd='', text=''):
            self.key = key
            self.cmd = cmd
            self.text = text

    class Fragment:
        def __init__(self, area, pos=(0, 0)):
            self.area = area
            self.x, self.y = pos
            self.width = area[3] - area[2]
            self.height = area[1] - area[0]

    def __init__(self, parent, title):
        self.parent = parent
        self.title = title
        self.options = []
        self.child = []
        self.pages = []
        self.img_str = ""
        self.item = None
        self.menu_cache = []
        self.sum_cache = []
        self.image = np.array([[" "] * Frame.width] * Frame.height)
        # self.color_map = np.array([[None] * Frame.width] * Frame.height)

        if self.parent is None:
            self.idx = 0
            self.frame_name = '0'
            self.template = Frame.home_template
        else:
            self.idx = len(parent.child)
            self.frame_name = self.parent.frame_name + 'z' + str(self.idx)
            self.template = Frame.category_template

        self.fragments = {}
        self.add_fragment('full', (0, Frame.height, 0, Frame.width))
        self.add_fragment('item', (3, 22, 46, 76))
        self.add_fragment('path', (1, 2, 2, 44))
        self.add_fragment('menu', (5, 22, 2, 10))
        self.add_fragment('price', (1, 2, 46, 76))
        self.add_fragment('summary', (5, 22, 12, 44))

        self.load_file(self.template, 'full')

        # insert path info
        frame = self
        path = ''
        while True:
            if frame.parent is not None: frame = frame.parent
            else: break
            path = '>' + frame.title + path
        self.replace(path, 'path')

    def __setitem__(self, key, value):
        if type(key) is int:
            self.child[key] = value
        elif type(key) is str:
            for idx, frame in enumerate(self.child):
                if frame.title is key:
                    self.child[idx] = value

    def __getitem__(self, x):
        if type(x) is int:
            return self.child[x]
        elif type(x) is str:
            for frame in self.child:
                if frame.title == x:
                    return frame
            self.child.append(Frame(self, x))
            return self.child[-1]
        else:
            print 'type of {} is {}, not int or str!'.format(x, type(x))

    def add_fragment(self, name, area):
        self.fragments[name] = (Frame.Fragment(area))

    def clear_fragment(self, frag_name):
        frag = self.fragments[frag_name]
        x1, x2, y1, y2 = frag.area
        frag.x = 0
        frag.y = 0
        self.replace(' ' * (x2 - x1) * (y2 - y1), frag_name)
        frag.x = 0
        frag.y = 0

    def recursive(self, cmd, ls='self.child + self.pages'):
        ret = []
        try: ret = [eval(cmd)]
        except AttributeError: pass
        for frame in eval(ls):
            ret += frame.recursive(cmd, ls)
        return ret

    def build(self):
        self.recursive('self.add_options()', 'self.child')
        self.recursive('self.add_menu_and_sum()', 'self.child')
        self.recursive('self.load_item()', 'self.child')
        self.recursive('self.build_img_str()')
        self.recursive('self.colorize_menu_and_sum()')
        self.recursive('self.colorize_item()')
        return ''.join(self.recursive('self.img_str')) + '^LE'

    @staticmethod
    def text2img(text, width):
        text = utils.text_to_win_big5(text)
        # convert text to fit area width
        lines = [line for l_line in text.split('\n') for line in textwrap.wrap(l_line, width, replace_whitespace=False)]
        return np.array([list(line.ljust(width)) for line in lines])

    # TODO This self-made replace sucks, try to find library
    def replace(self, string, frag_name):
        # print string.decode('big5')
        # os.system('pause')
        try: frag = self.fragments[frag_name]
        except KeyError: return
        area = frag.area
        roi = self.image[area[0]:area[1], area[2]:area[3]]
        str_idx = 0
        while str_idx < len(string):
            char_length = 2 if '\x81' <= string[str_idx] <= '\xfe' else 1
            char = string[str_idx:str_idx + char_length]
            str_idx += char_length

            if char == '\n':
                frag.x, frag.y = frag.x + 1, 0
                continue

            i = 0
            char_num = len(char)
            while i < char_num:  # Handle multi-byte big5 char
                try:
                    roi[frag.x, frag.y] = char[i]
                    frag.y += 1
                    i += 1
                except IndexError as e:
                    if e.message.find('axis 0') > 0:  # Not enough lines
                        return string[str_idx - char_num:]  # Return remaining string for new page
                    elif e.message.find('axis 1') > 0:  # Not enough column
                        # Delete half char & roll back
                        if i == 1:
                            roi[frag.x, frag.y - 1] = ' '
                            i -= 1
                        # New line
                        frag.x += 1
                        frag.y = 0

    def load_file(self, filename, frag_name):
        with codecs.open(filename, encoding='big5') as textFile:
            text = textFile.read()
        # Delete Beginning of pcman .ans file
        if text[:3] == '\x1b[m': text = text[3:]

        text = utils.text_to_win_big5(text)

        self.replace(text, frag_name)

    def load_item(self):
        if self.item is None: return
        item = self.item

        # Load price info to price fragment
        price_str = ''
        if item.buyout != '':
            price_str += '直購價:' + item.buyout + '  '
        if item.current_bid != '':
            price_str += '當前出價:' + item.current_bid
        elif item.start_bid != '':
            price_str += '起標價:' + item.start_bid
        if price_str == '':
            price_str = '本商品無價格資訊，已違反板規！'
        self.replace(price_str, 'price')

        # Load item info to item fragment
        remain = self.replace(item.text, 'item')
        while remain is not None:
            npage = self.new_page()
            npage.clear_fragment('item')
            remain = npage.replace(remain, 'item')
            self.pages.append(npage)

    def add_pmore_option(self, key='', cmd='', text=''):
        self.options.append(Frame.Option(key, cmd, text))

    def add_options(self):
        if len(self.child) > 0:
            self.add_pmore_option(Frame.keyEnter, ":" + self.child[0].frame_name + ":")
        for idx, sub in enumerate(self.child):
            sub_num = len(self.child)
            sub.add_pmore_option(Frame.keyNext, ":" + self.child[(idx + 1) % sub_num].frame_name + ":")
            sub.add_pmore_option(Frame.keyPrev, ":" + self.child[(idx - 1) % sub_num].frame_name + ":")
            sub.add_pmore_option(Frame.keyBack, ":" + self.frame_name + ":")

    def add_menu_and_sum(self):
        if self.parent is None: return
        max_item = self.fragments['menu'].height
        max_sum_len = self.fragments['summary'].width
        page_num = self.idx / max_item
        try:
            menu = self.parent.menu_cache[page_num]
            summary = self.parent.sum_cache[page_num]
        except IndexError:
            begin = page_num * max_item
            end = max(self.idx, (page_num + 1) * max_item)
            menu = ''
            summary = ''
            for frame in self.parent.child[begin:end]:
                menu += frame.title.center(self.fragments['menu'].width, ' ') + '\n'
                if frame.item is not None:
                    short_sum = frame.item.summary
                    try:
                        short_sum = short_sum[:max_sum_len].decode('big5')
                    except UnicodeDecodeError:
                        short_sum = short_sum[:max_sum_len - 1].decode('big5')
                    summary += short_sum.encode('big5') + '\n'
            self.parent.menu_cache.append(menu)
            self.parent.sum_cache.append(summary)
        self.replace(menu, 'menu')
        self.replace(summary, 'summary')
        # Replace full summary of the item itself
        if self.item is not None:
            local_idx = self.idx % max_item
            sum_frag = self.fragments['summary']
            sum_frag.x, sum_frag.y = local_idx, 0
            self.replace(self.item.summary, 'summary')
            rest = sum_frag.width - sum_frag.y
            self.replace(' ' * rest, 'summary')

    def build_img_str(self):
        self.img_str = "^L:" + self.frame_name + ":" + \
                       "".join(["#{},{},{}".format(option.key, option.cmd, option.text) for option in self.options]) + \
                       "#\n" + "\n".join(["".join(line) for line in self.image]) + "\n\n"

    # def colorize(self):
    #     for img_line, color_line in zip(self.image, self.color_map):
    #         start = end = 0
    #         while True:
    #             if end == len(color_line) or color_line[start] != color_line[end]:
    #                 code = color_line[start]
    #                 sub_string = ''.join(img_line[start:end])
    #                 if code is None:
    #                     self.img_str += sub_string
    #                 else:
    #                     self.img_str += "\x1b[{}m{}\x1b[m".format(code, sub_string)
    #                 start = end
    #                 if end == len(color_line): break
    #             else: end += 1
    #         self.img_str += '\r\n'

    def colorize(self, string, code, start=0):
        pos = self.img_str.find(string, start)
        if pos >= 0:
            self.img_str = "{}\x1b[{}m{}\x1b[m{}".format(self.img_str[:pos], code, string,
                                                         self.img_str[pos + len(string):])

    def colorize_menu_and_sum(self):
        self.colorize(self.title, Item.color_code['Menu'])
        if self.item is not None:
            s = self.item.summary
            start = self.img_str.find(self.item.get_full_id())
            while s != '':
                length = self.fragments['summary'].width
                if len(s) < length: s += ' ' * (length - len(s))
                try: s[:length].decode('big5')
                except UnicodeDecodeError: length -= 1
                self.colorize(s[:length], Item.color_code['Menu'], start)
                s = s[length:]

    #TODO
    # def colorize_item(self):
    #     pass
    #     if self.item is None:
    #         return
    #     item = self.item
    #     # Colorize title according to rarity
    #     self.colorize(item.name, Item.color_code[item.rarity])
    #     self.colorize(item.sub_type, Item.color_code[item.rarity])

    def item_exist(self, item):
        for frame in self.child:
            if frame.item.raw_text == item.raw_text:
                return True
        return False

    def new_page(self):
        npage = Frame(self, self.title)
        npage.frame_name = self.frame_name + 'p' + str(len(self.pages) + 2)
        # npage.child = self.child
        npage.options = self.options
        npage.fragments = self.fragments
        npage.image = np.copy(self.image)
        npage.item = self.item

        ppage = self.pages[-1] if bool(self.pages) else self

        ppage.options = [option for option in ppage.options if option.key != (Frame.keyPageDown or Frame.keyPageUp)]
        npage.options = [option for option in npage.options if option.key != (Frame.keyPageDown or Frame.keyPageUp)]
        ppage.add_pmore_option(Frame.keyPageDown, ":" + npage.frame_name + ":")
        npage.add_pmore_option(Frame.keyPageUp, ":" + ppage.frame_name + ":")

        return npage

'''
    def add_item(self, title, level):
        color = "{}\x1b[1;31m{}\x1b[m\n" if title is self.title else "{}{}\n"
        self.replace(self.fragments[1], color.format(Frame.indent*level, title))
        for frame in self.subFrames:
            frame.add_item(title, level)
    def construct_sub(self, level):
        subNum = len(self.subFrames)
        if subNum > 0:
            self.add_pmore_option(Frame.keyEnter, ":"+self.subFrames[0].name+":", "")

        for idx, frame in enumerate(self.subFrames):
            for f in self.subFrames:
                f.add_menu_item(frame.title, level+1)
            frame.construct_sub(level+1)
            frame.add_pmore_option(Frame.keyNext, ":"+self.subFrames[(idx+1) % subNum].name+":", "")
            frame.add_pmore_option(Frame.keyPrev, ":"+self.subFrames[(idx-1) % subNum].name+":", "")
            frame.add_pmore_option(Frame.keyBack, ":"+self.name+":", "")

    def construct(self):
        self.addressing("", 0)
        self.add_menu_item(self.title, 0)
        self.construct_sub(0)
'''

if __name__ == '__main__':
    f = Frame(None, '')
    t = '''1.通貨單位使用小寫
2.時間格式 12/21 01:27
3.跨年交易x
4.雖然商店裡顯示的編號是全形，但是推文必須用半形XD
5.可以有空白
6.備註請多一條/
7.推錯處理方式：如果店長認同買方推錯，請將"整串"推文複製貼上到記事本，刪除該行推文，然後再次複製並重頭開始分析
（須將商店狀態重設）
8.ign推過一次後可省略（連同'/'）
'''
    img = Frame.text2img(t, 30)
    f.image = img
    f.build_img_str()
    print f.img_str.replace('\n', '\r\n').decode('big5')

    # root = Frame(None, "物品")
    # root["武器"]["單手劍"]["劍一"]
    # root["武器"]["單手劍"]["劍二"]
    # root["武器"]["弓"]["弓一"]
    # root["武器"]["弓"]["弓二"]
    # root["防具"]["頭盔"]["頭一"]
    # root["防具"]["頭盔"]["頭二"]
    # root["防具"]["鞋子"]["０１"]
    # root["防具"]["鞋子"]["０２"]
    # root["防具"]["鞋子"]["０３"]
    # root["防具"]["鞋子"]["０４"]
    # root["防具"]["鞋子"]["０５"]
    # root["防具"]["鞋子"]["０６"]
    # root["防具"]["鞋子"]["０７"]
    # root["防具"]["鞋子"]["０８"]
    # root["防具"]["鞋子"]["０９"]
    # root["防具"]["鞋子"]["１０"]
    # root["防具"]["鞋子"]["１１"]
    # root["防具"]["鞋子"]["１２"]
    # root["防具"]["鞋子"]["１３"]
    # root["防具"]["鞋子"]["１４"]
    # root["防具"]["鞋子"]["１５"]
    # root["防具"]["鞋子"]["１６"]
    # root["防具"]["鞋子"]["１７"]
    # root["防具"]["鞋子"]["１８"]
    # root["防具"]["鞋子"]["１９"]
    # root["防具"]["鞋子"]["２０"]
    # root.build()