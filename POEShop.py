# coding=big5
import os
import collections
import re
import datetime
import sys

import pyperclip
import wx

from Frame import Frame
from Item import Item
import utils



# TODO File Manager, Category Order, Item Color
class PoeShop(wx.Frame):
    push_pattern = re.compile(r'.+? (.+?)\s*:'  # push and ptt id
                              r'\s*([\d,]+)\s*'  # bid items
                              r'\/\s*([\w,]+)\s*'  # bid price
                              r'(?:\/\s*([^\/\s]+)\s*)?'  # ign
                              r'(?:\/\s*(.*?)\s*)?'  # note
                              r'(\d{2}\/\d{2} \d{2}\:\d{2})')  # date time

    def __init__(self, parent, title):
        super(PoeShop, self).__init__(parent, title=title, size=(750, 350))
        self.new_item = None
        self.rootPath = utils.shop_path
        self.item_count = sum([len(files) for _, _, files in os.walk(self.rootPath)])
        self.default_path = '[category]\[type]'
        self.default_sum = ''
        self.default_bo = ''
        self.default_sb = ''
        self.default_end = ''
        self.recent_path = collections.deque(maxlen=5)
        self.recent_sum = collections.deque(maxlen=5)
        self.recent_bo = collections.deque(maxlen=5)
        self.recent_sb = collections.deque(maxlen=5)
        self.recent_end = collections.deque(maxlen=5)

        self.item_list = {}
        for root, _, files in os.walk(self.rootPath):
            for item_file in files:
                path = os.path.join(root, item_file)
                item = Item.load(path)
                self.item_list[item.id] = (item, path)

        self.clipText = ''
        text = pyperclip.paste()
        if text is not None:
            self.clipText = text
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.check_new_item, self.timer)
        self.timer.Start(500)

        self.init_ui()
        self.Centre()
        self.ToggleWindowStyle(wx.STAY_ON_TOP)
        self.Show()

    def init_ui(self):

        panel = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)

        fgs = wx.FlexGridSizer(6, 3, 12, 12)

        name_label = wx.StaticText(panel, label='名稱')
        path_label = wx.StaticText(panel, label='分類')
        sum_label = wx.StaticText(panel, label='簡介')
        bo_label = wx.StaticText(panel, label='直購')
        sb_label = wx.StaticText(panel, label='起標')
        end_label = wx.StaticText(panel, label='結束')

        self.name_text = wx.StaticText(panel)
        self.path_cb = wx.ComboBox(panel, choices=self.recent_path)
        self.sum_cb = wx.ComboBox(panel, choices=self.recent_sum)
        self.bo_cb = wx.ComboBox(panel, choices=self.recent_bo)
        self.sb_cb = wx.ComboBox(panel, choices=self.recent_sb)
        self.end_cb = wx.ComboBox(panel, choices=self.recent_end)

        self.path_btn = wx.Button(panel, -1, '設為預設值')
        self.sum_btn = wx.Button(panel, -1, '設為預設值')
        self.bo_btn = wx.Button(panel, -1, '設為預設值')
        self.sb_btn = wx.Button(panel, -1, '設為預設值')
        self.end_btn = wx.Button(panel, -1, '設為預設值')

        self.Bind(wx.EVT_BUTTON, self.set_default, self.path_btn)
        self.Bind(wx.EVT_BUTTON, self.set_default, self.sum_btn)
        self.Bind(wx.EVT_BUTTON, self.set_default, self.bo_btn)
        self.Bind(wx.EVT_BUTTON, self.set_default, self.sb_btn)
        self.Bind(wx.EVT_BUTTON, self.set_default, self.end_btn)

        fgs.AddMany([name_label, self.name_text, wx.StaticText(panel),
                     path_label, (self.path_cb, 1, wx.EXPAND), self.path_btn,
                     sum_label, (self.sum_cb, 1, wx.EXPAND), self.sum_btn,
                     bo_label, (self.bo_cb, 1, wx.EXPAND), self.bo_btn,
                     sb_label, (self.sb_cb, 1, wx.EXPAND), self.sb_btn,
                     end_label, (self.end_cb, 1, wx.EXPAND), self.end_btn])

        fgs.AddGrowableCol(1, 1)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        update_btn = wx.Button(panel, -1, '更新商品')
        del_btn = wx.Button(panel, -1, '刪除商品')
        gen_btn = wx.Button(panel, -1, '產生商店')
        parse_btn = wx.Button(panel, -1, '分析推文')
        self.Bind(wx.EVT_BUTTON, self.update_item, update_btn)
        self.Bind(wx.EVT_BUTTON, self.delete_item, del_btn)
        self.Bind(wx.EVT_BUTTON, self.gen_shop, gen_btn)
        self.Bind(wx.EVT_BUTTON, self.parse_push, parse_btn)

        hbox.AddMany([(update_btn, 0, wx.ALL, 5), (del_btn, 0, wx.ALL, 5),
                      (parse_btn, 0, wx.ALL, 5), (gen_btn, 0, wx.ALL, 5)])

        vbox.Add(fgs, flag=wx.ALL | wx.EXPAND, border=10)
        vbox.Add(hbox, flag=wx.ALL | wx.EXPAND, border=10)

        log = wx.TextCtrl(panel, -1, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        sys.stdout = RedirectText(log)

        hb = wx.BoxSizer(wx.HORIZONTAL)
        hb.Add(vbox, flag=wx.ALL | wx.EXPAND, border=10)
        hb.Add(log, proportion=1, flag=wx.ALL | wx.EXPAND, border=10)

        panel.SetSizer(hb)

    def check_new_item(self, e):
        # Check if clipboard content has changed
        text = pyperclip.paste()
        if self.clipText == text:
            return
        self.clipText = text
        if text is not None:
            text = utils.text_to_win_big5(text)

        try:
            assert Item.item_pattern.match(text) is not None, "string didn't match item's pattern!"
            item = Item(text)
        except (AssertionError, TypeError): return

        item.translate_path(self.default_path)
        self.item_count += 1
        item.id = self.item_count
        self.new_item = item
        self.path_cb.SetValue(item.path)
        self.sum_cb.SetValue(item.summary)
        self.bo_cb.SetValue(self.default_bo)
        self.sb_cb.SetValue(self.default_sb)
        self.end_cb.SetValue(self.default_end)
        self.name_text.SetLabelText(item.name + ' ' + item.sub_type)
        self.update_item(None)

    def update_item(self, e):
        item = self.new_item
        # Update item info
        item.summary = self.update_combo_box(self.sum_cb, self.recent_sum)
        item.buyout = self.update_combo_box(self.bo_cb, self.recent_bo)
        item.start_bid = self.update_combo_box(self.sb_cb, self.recent_sb)
        item.bid_end_time = self.update_combo_box(self.end_cb, self.recent_end)
        if item.start_bid != '': item.bidding = True
        # Update translated item path
        old_abs_path = os.path.join(self.rootPath, item.relative_file_path())
        raw_path = self.update_combo_box(self.path_cb, self.recent_path)
        if not item.translate_path(raw_path):  # provided path variable cannot translate
            print 'Path variable cannot be translated!'
            return
        abs_path = os.path.join(self.rootPath, item.relative_file_path())
        if abs_path != old_abs_path and os.path.exists(old_abs_path):
            os.remove(old_abs_path)
            # Delete empty left behind
            dir_path = os.path.dirname(old_abs_path)
            while dir_path != self.rootPath:
                if len(os.listdir(dir_path)) == 0:
                    os.rmdir(dir_path)
                dir_path = dir_path[:dir_path.rfind('\\')]
        # Make dir for new item txt and write info
        dirname = os.path.dirname(abs_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        item.save(abs_path)
        self.item_list[item.id] = (item, abs_path)

    def delete_item(self, e):
        item = self.new_item
        abs_path = os.path.join(self.rootPath, item.relative_file_path())
        os.remove(abs_path)
        self.item_count -= 1
        self.item_list.pop(item.id)
        # Delete empty folder left behind
        dir_path = os.path.dirname(abs_path)
        while dir_path != self.rootPath:
            if len(os.listdir(dir_path)) == 0:
                os.rmdir(dir_path)
            dir_path = dir_path[:dir_path.rfind('\\')]
        # Clear item info on UI
        self.path_cb.SetValue('')
        self.sum_cb.SetValue('')
        self.bo_cb.SetValue('')
        self.sb_cb.SetValue('')
        self.end_cb.SetValue('')
        self.name_text.SetLabelText('')

    @staticmethod
    def update_combo_box(combo_box, recent_list):
        string = combo_box.GetValue()
        if string == '': return string
        string = utils.text_to_win_big5(string)
        if string in recent_list: recent_list.remove(string)
        recent_list.appendleft(string)
        combo_box.SetItems(recent_list)
        combo_box.SetValue(recent_list[0])
        return string

    def set_default(self, e):
        eid = e.GetId()
        if eid == self.path_btn.GetId():
            self.default_path = utils.text_to_win_big5(self.path_cb.GetValue())
        elif eid == self.sum_btn.GetId():
            self.default_sum = utils.text_to_win_big5(self.sum_cb.GetValue())
        elif eid == self.bo_btn.GetId():
            self.default_bo = utils.text_to_win_big5(self.bo_cb.GetValue())
        elif eid == self.sb_btn.GetId():
            self.default_sb = utils.text_to_win_big5(self.sb_cb.GetValue())
        elif eid == self.end_btn.GetId():
            self.default_end = utils.text_to_win_big5(self.end_cb.GetValue())

    def gen_shop(self, e):
        root = Frame(None, "首頁")
        for item_id in sorted(self.item_list.keys()):
            item, path = self.item_list[item_id]
            hierarchy = os.path.dirname(path)[len(self.rootPath) + 1:].split('\\')
            node = root
            for part in hierarchy: node = node[part]
            node[item.get_full_id().center(root.fragments['menu'].width)].item = item

        root.recursive('self.add_options()', 'self.child')
        root.recursive('self.add_menu_and_sum()', 'self.child')
        root.recursive('self.load_item()', 'self.child')

        root.add_fragment('main', (2, Frame.height - 2, 2, Frame.width - 2))
        root.fragments['main'].x = Frame.height - 4
        root.fragments['main'].y = Frame.width - 4
        remain = root.replace(self.get_report(), 'main')
        while remain is not None:
            npage = root.new_page()
            npage.clear_fragment('main')
            remain = npage.replace(remain, 'main')
            root.pages.append(npage)

        root.recursive('self.build_img_str()')
        root.recursive('self.colorize_menu_and_sum()')
        root.recursive('self.colorize_item()')
        img_str = ''.join(root.recursive('self.img_str')) + '^LE'

        pyperclip.copy(img_str.replace('\n', '\r\n'))

        print 'Shop generated successfully!'

    # TODO push error, ign cache save
    def parse_push(self, e):
        push_texts = utils.text_to_win_big5(pyperclip.paste())
        ign_cache = {}
        time = None
        for push in push_texts.split('\n'):
            print push
            # Parse a push and load related item
            ign = None
            try:
                ptt_id, bid_id_list, bid_price_list, ign, note, time = PoeShop.push_pattern.match(push).groups()
                bil = bid_id_list.split(',')
                bpl = bid_price_list.split(',')
                assert len(bil) >= len(bpl)
                bpl.extend([bpl[-1]] * (len(bil) - len(bpl)))
            except:
                print 'Not a valid bidding push. Skip.'
                continue

            # Save ign to cache
            if bool(ign): ign_cache[ptt_id] = ign
            else:
                try: ign = ign_cache[ptt_id]
                except KeyError:
                    print push + 'In game name of ptt user:' + ptt_id + ' has never been provided!'
                    continue

            # Close all bid that has ended
            now = datetime.datetime.today()
            push_time = datetime.datetime.strptime(time, '%m/%d %H:%M')
            push_time.replace(year=now.year)
            for item, path in self.item_list.values():
                # Check if item bidding has ended
                if not item.bidding: continue
                end_time = datetime.datetime.strptime(item.bid_end_time, '%m/%d %H:%M')
                end_time.replace(year=now.year)
                if push_time >= end_time:
                    item.bidding = False

            # update bid info for every id-price pair
            for item_id, bid_str in zip(bil, bpl):
                try:
                    item, path = self.item_list[int(item_id)]
                    nb = Item.parse_price(bid_str)
                    assert bool(nb)
                    assert item.bidding
                except KeyError:
                    print push + 'Item number: ' + item_id + ' is not in the shop!'
                    continue
                except AssertionError: continue

                # TODO cross year bidding is not supported
                # Check close-to-end bidding
                end_time = datetime.datetime.strptime(item.bid_end_time, '%m/%d %H:%M')
                end_time.replace(year=now.year)
                if end_time - push_time <= datetime.timedelta(minutes=10):
                    end_time += datetime.timedelta(minutes=10)
                    item.bid_end_time = end_time.strftime('%m/%d %H:%M')

                # Compare new bid with start bid, current bid, and buyout
                sb = Item.parse_price(item.start_bid)
                cb = Item.parse_price(item.current_bid)
                bo = Item.parse_price(item.buyout)
                # TODO This if condition sucks... find a more simple way
                if (bool(bo) and nb > bo) or (bool(cb) and nb > cb) or (not bool(cb) and nb >= sb):
                    if item.bid_count == '': item.bid_count = 0
                    item.current_bid, item.current_bidder, item.bid_count = bid_str, ign, item.bid_count + 1
                    if bool(bo) and nb >= bo:
                        item.current_bid = bo
                        item.bidding = False

        self.push_update_time = time

        for item, path in self.item_list.values():
            item.save(path)
        print 'pushes parsed successfully!'
        print self.get_report().decode('big5')

    def get_report(self):
        title = '\n{:4s}  {:>8s}  {:16s}{:8s}  {:11s}'.format(
            '編號', '當前價', '當前得標者', '出價次數', '結標時間')
        bidding = ''
        ended = ''
        for item, _ in sorted(self.item_list.values(), key=lambda x: x[0].bid_count, reverse=True):
            if not bool(item.current_bidder): continue
            data = '\n{:4d}  {:>8s}  {:16s}{:8d}  {:11s}'.format(
                item.id, item.current_bid, item.current_bidder,
                item.bid_count, item.bid_end_time)
            if item.bidding: bidding += data
            else: ended += data
        return '更新時間： (此區資訊無法即時更新，僅供參考，競標請以推文為準。)' \
               + '\n\n競標中' + title + bidding \
               + '\n\n已結標' + title + ended


class RedirectText:
    def __init__(self, aWxTextCtrl):
        self.out = aWxTextCtrl
    def write(self, string):
        self.out.WriteText(string)

if __name__ == '__main__':
    app = wx.App()
    PoeShop(None, title='POE Shop Generator')
    app.MainLoop()