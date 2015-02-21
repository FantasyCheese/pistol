# coding=big5
import codecs
import os
import re

from pint import UnitRegistry, UndefinedUnitError

import utils


class Item:
    item_type_path = os.path.join(utils.data_path, 'item_type.txt')
    affix2abbr_path = os.path.join(utils.data_path, 'affix2abbr.txt')
    currency_rate_path = os.path.join(utils.data_path, 'currency_rate.txt')

    with codecs.open(item_type_path, encoding='big5') as textFile:
        text = textFile.read()
    type_data = utils.text_to_win_big5(text).split('\n')

    item_pattern = re.compile("(?s)Rarity:.*?\n"
                              r"--------\n"
                              r"(?:.*?\n"
                              r"--------\n)?"
                              r"(?:需求:.*?\n"
                              r"--------\n)?"
                              r"(?:Sockets: .*?\n"
                              r"--------\n)?"
                              r"(?:Itemlevel: .*?\n)?")

    price_pattern = re.compile(r'(\d+)(\D{1,3})')

    with open(affix2abbr_path, 'rb') as textFile:
        text = utils.text_to_win_big5(textFile.read()).split('\n\n')[0]
    affix2abbr = {}
    for line in text.split('\n'):
        affix, abbr = line.split(' => ')
        affix = affix.replace('+', '\+').replace('X', '(\d+)').decode('big5')
        affix2abbr[affix] = abbr

    color_code = dict(Normal='1', Magic='36', Rare='1;33', Unique='31', Menu='1;31')

    ureg = UnitRegistry(currency_rate_path)

    attr_list = ('[category]', '[type]', '[sub_type]', '[buyout]', '[start_bid]', '[current_bid]')

    def __init__(self, text):
        self.id = None
        # self.id_full = None

        self.raw_text = text
        lines = text.split('\n')
        self.rarity = lines[0][8:]
        self.name = lines[1]

        global types
        for types in self.type_data:
            if types.find(lines[2]) >= 0:
                break

        item_type = types.split('	')
        self.category = item_type[0]
        self.type = item_type[1]
        self.sub_type = lines[2]

        self.path = ''
        self.buyout = ''
        self.start_bid = ''
        self.current_bid = ''
        self.current_bidder = ''
        self.bid_count = 0
        self.bid_end_time = ''
        self.bidding = False

        # TODO Change to simplified text on colorize mod
        t = self.raw_text
        # join type and name
        t = t.split('\n')
        t[1] += ' ' + t[2]
        del t[2]
        t = '\n'.join(t)
        # Eliminate (augmented) & (unmet)
        t = re.sub(r'\s\(.*\)', '', t)
        # join requirement lines
        t = t.replace('\n等級: ', '等級:')
        t = t.replace('\n智慧: ', ' 智慧:')
        t = t.replace('\n力量: ', ' 力量:')
        t = t.replace('\n敏捷: ', ' 敏捷:')
        # delete redundant separation lines
        t = re.sub('\n--------\nSockets:', '\n連線:', t)
        t = re.sub('\n--------\nItemlevel:', ' 物品等級:', t)
        self.text = t

        self.summary = self.gen_sum(self.raw_text)

    def relative_file_path(self):
        return os.path.join(self.path, '{}-{}.txt'.format(self.id, self.name))

    @staticmethod
    def gen_sum(text):
        summary = ''
        for line in text.split('\n'):
            for affix, abbr in Item.affix2abbr.items():
                m = re.match(affix, line.decode('big5'))
                if m is not None:
                    summary += abbr.replace('X', m.group(1).encode('big5')) + ' '
        return summary.strip()

    @staticmethod
    def load(path):
        with codecs.open(path, encoding='big5') as text_file:
            header, data = utils.text_to_win_big5(text_file.read()).split('\n\n')

        item = Item(data)
        item.id = int(os.path.basename(path).split('-')[0])
        item.summary, item.buyout, item.start_bid, item.current_bid, \
            item.current_bidder, item.bid_count, item.bid_end_time, bidding = \
            [line.split('：')[1] if len(line.split('：')) > 1 else '' for line in header.split('\n')]
        item.bidding = True if bidding == 'True' else False
        item.bid_count = int(item.bid_count) if bool(item.bid_count) else 0
        return item

    def save(self, path):
        with open(path, mode='w') as textFile:
            textFile.write('簡介：{}\n直購價：{}\n起標價：{}\n當前標價：{}\n'
                           '當前得標者：{}\n出價次數：{}\n結標時間：{}\n競標中：{}\n\n{}'
                           .format(self.summary, self.buyout, self.start_bid, self.current_bid, self.current_bidder,
                                   self.bid_count, self.bid_end_time, str(self.bidding), self.raw_text))

    @staticmethod
    def parse_price(text):
        if text == '': return
        price_list = Item.price_pattern.findall(text)
        if price_list is None:
            print text, u'\n出價格式錯誤！'
            return
        bid = 0 * Item.ureg.c
        for quantity, unit in price_list:
            try:
                bid += float(quantity) * eval('Item.ureg.' + unit.lower())
            except UndefinedUnitError:
                print u'通貨單位 ', unit, u'未登錄！'
                return
            except TypeError:
                print u'格式錯誤！'
                return
        return bid

    def translate_path(self, path):
        for attr in Item.attr_list:
            if attr in path:
                item_attr = eval('self.' + attr[1:-1])
                if item_attr == '':
                    print 'The item attribute ' + attr + ' is empty!'
                    return False
                else:
                    path = path.replace(attr, item_attr)
        self.path = path
        return True

    def get_full_id(self):
        return ''.join([unichr(0xFEE0 + ord(digit)).encode('big5') for digit in str(self.id)])