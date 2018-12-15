from tkinter.ttk import Separator
from tkinter import Menu
import tkinter
import pickle
from os import listdir
from os.path import isfile, join

from objects import Market, Coin, Alert
from popups import *
from utils import RepeatedTimer, format_dollar, format_satoshi
from calls import get_last_price

root = tkinter.Tk()
ico_ = "mao.ico"


class Overview:

    def __init__(self, master):
        self._NAME = "Coinz.py"
        self._SOUNDS = "sounds"
        self._ICO = ico_

        self.master = master
        self.master.title(self._NAME)

        self.sound_name = "default.wav"
        self.sound_array = self.get_sounds()

        self.settings = {
            "default_exchange": "Bittrex",
            "timer_interval": "15",
            "sound_name": self.sound_name
        }
        root.protocol("WM_DELETE_WINDOW", self.on_closing)

        if os.path.exists(os.path.join(os.getcwd(), "settings.pickle")):
            with open('settings.pickle', 'rb') as f:
                self.settings = pickle.load(f)

        print(self.settings)

        print(self.sound_array)

        ind = next(iter(
            [i for i in range(len(self.sound_array)) if self.sound_array[i].find(self.settings["sound_name"]) != -1]),
                   None)
        if ind is None:
            ErrorPopup(self.master, "saved sound " + self.settings[
                "sound_name"] + " not found! \\n it will be replaced with the default on close")
            self.settings["sound_name"] = self.sound_name

        self.market_prices = {
            # btc and eth price sources can change but bnb will always be binance
            'btc': get_last_price[self.settings["default_exchange"]]("usdt", "btc"),
            'eth': get_last_price[self.settings["default_exchange"]]("usdt", "eth"),
            'bnb': get_last_price['Binance']("usdt", "bnb")
        }
        t_i = self.settings["timer_interval"]
        self.rt = RepeatedTimer(15 if (t_i == '') else int(t_i), self.update_coins)
        self.coin_list = []

        # create menu_bar
        self.menu_bar = Menu(master)
        self.settings_menu = Menu(self.menu_bar, tearoff=0)
        self.settings_menu.add_command(label="Settings", command=self.edit_settings)
        # self.settings_menu.add_command(label="Sounds", command=self.edit_sounds)
        self.menu_bar.add_cascade(label="File", menu=self.settings_menu)

        root.config(menu=self.menu_bar)

        # create treeview
        ct_header = ["exchange", "market", "shitcoin", "market price", "usd price", "alerts"]
        ct_width = [80, 80, 128, 100, 100, 40]
        self.cointree = Treeview(master, selectmode="browse", columns=ct_header, show="headings")
        for i in range(len(ct_header)):
            self.cointree.heading(ct_header[i], text=ct_header[i])
            self.cointree.column(ct_header[i], width=ct_width[i], stretch=False)
        self.cointree.grid(column=0, row=0, columnspan=6, rowspan=6)

        # create buttons
        button_frame = Frame(master)

        self.add_coin_button = Button(button_frame, text="Add Coin", command=self.add_coin)
        self.add_coin_button.grid(column=0, row=0, sticky="NEWS")
        self.remove_coin_button = Button(button_frame, text="Remove Coin", command=self.remove_coin)
        self.remove_coin_button.grid(column=0, row=1, sticky="NEWS")
        self.button_separator = Separator(button_frame, orient="horizontal")
        self.button_separator.grid(column=0, row=2, sticky="NEWS", pady=5)
        self.add_alert_button = Button(button_frame, text="Add Alert", command=self.add_alert)
        self.add_alert_button.grid(column=0, row=3, sticky="NEWS")
        self.view_alerts_button = Button(button_frame, text="View Alerts", command=self.view_alerts)
        self.view_alerts_button.grid(column=0, row=4, sticky="NEWS")

        button_frame.grid(column=6, row=0)

        # status label
        status_frame = Frame(master)
        self.status_info_text = StringVar()
        self.status_info_text.set(self.settings["default_exchange"])
        self.status_price_text = StringVar()
        self.status_price_text.set("example price")
        self.status_info = Label(status_frame, relief="sunken", textvariable=self.status_info_text)
        self.status_price = Label(status_frame, relief="sunken", textvariable=self.status_price_text)
        self.status_info.grid(column=0, row=0)
        self.status_price.grid(column=1, row=0)
        status_frame.grid(column=0, row=6, columnspan=6)
        ##load shit

        if os.path.exists(os.path.join(os.getcwd(), "coinlist.pickle")):
            with open('coinlist.pickle', 'rb') as f:
                self.coin_list = pickle.load(f)

        # update treeview
        self.display_coinlist(True)

    def edit_settings(self):
        self.edit_settings_popup = EditSettingsPopup(self, self.master)
        self.master.wait_window(self.edit_settings_popup.top)

    def get_sounds(self):
        sound_array = []
        for sound in [f for f in listdir(self._SOUNDS) if isfile(join(self._SOUNDS, f))]:
            sound_array.append(join(self._SOUNDS, sound))
        return sound_array

    def update_coins(self):
        # update btc price and btc display
        self.market_prices = {
            # btc and eth price sources can change but bnb will always be binance
            'btc': get_last_price[self.settings["default_exchange"]]("usdt", "btc"),
            'eth': get_last_price[self.settings["default_exchange"]]("usdt", "eth"),
            'bnb': get_last_price['Binance']("usdt", "bnb")
        }
        self.status_info_text.set(self.settings["default_exchange"])
        self.status_price_text.set(("BTC: " + format_dollar(self.market_prices['btc'])))
        # update coin objects
        for c in self.coin_list:
            if c.market is not Market.USDT.name:
                c.market_price = format_satoshi(get_last_price[c.exchange](c.market, c.name))
                c.usd_price = format_dollar(
                    get_last_price[c.exchange](c.market, c.name) * self.market_prices[c.market.lower()])
            else:
                c.market_price = format_dollar(get_last_price[c.exchange](c.market, c.name))
                c.usd_price = "-"
            # this will return alert events if any are tripped
            alert_events = c.check_alerts()
            if alert_events is not None and len(alert_events) > 0:
                # dont spam alert sounds, one will suffice
                self.master.deiconify()
                self.master.focus_force()
                self.play_notification_sound()
                # display each one
                for a in alert_events:
                    AlertPopup(self.master, c, a.info)
            # coin object is updated, time to update display
            item = self.find_item_from_coin(c)
            if item is None:
                ErrorPopup(self.master, "item not found!")
                return
            self.cointree.set(item, column="market price", value=c.market_price)
            self.cointree.set(item, column="usd price", value=c.usd_price)
            self.cointree.set(item, column="alerts", value=len(c.alerts))

    def add_coin(self):
        self.add_coin_popup = AddCoinPopup(self.master, self)
        self.add_coin_button["state"] = "disabled"
        self.master.wait_window(self.add_coin_popup.top)
        self.add_coin_button["state"] = "normal"

        ##check if user did not fill out form
        if not hasattr(self.add_coin_popup, "value"):
            print("no value 'value' in add_coin_popup")
            return
        # get ticker from input
        c_form = self.add_coin_popup.value
        print(c_form)

        for c in self.coin_list:
            if c_form[2].lower() is c.name.lower() and c_form[0].lower() is c.exchange.lower() \
                    and c_form[1].lower() is c.market.lower():
                InfoPopup(self.master, "You already added this coin!")
                return

        _market_price = 0
        _usd_price = 0

        if c_form[1] is not Market.USDT.name:
            _market_price = format_satoshi(get_last_price[c_form[0]](c_form[1], c_form[2]))
            _usd_price = format_dollar(
                get_last_price[c_form[0]](c_form[1], c_form[2]) * self.market_prices[c_form[1].lower()])
        else:
            _market_price = format_dollar(get_last_price[c_form[0]](c_form[1], c_form[2]))
            _usd_price = "-"

        _coin = Coin(
            c_form[2].upper(),
            c_form[0],
            c_form[1],
            _market_price,
            _usd_price)

        self.coin_list.append(_coin)

        self.display_coinlist(False)

    def remove_coin(self):
        selected_coin = self.cointree.selection()[0] if len(self.cointree.selection()) > 0 else None
        # if shit in None show a popup
        if selected_coin is None:
            InfoPopup(self.master, "You must select a coin to remove it!")
            return
        # do you wanna do dis?
        are_you_sure = AreYouSurePopup(self.master, "remove " + self.cointree.item(selected_coin)["values"][2])
        self.remove_coin_button["state"] = "disabled"
        self.master.wait_window(are_you_sure.top)
        self.remove_coin_button["state"] = "normal"
        remove_successful = False
        if are_you_sure.value:
            coin = self.find_coin_from_item(selected_coin)
            if coin is None:
                ErrorPopup(self.master, "could not find coin")
            # found it
            # remove from treeview
            self.cointree.delete(selected_coin)
            # remove from coinlist
            self.coin_list = [x for x in self.coin_list if x != coin]
            # ool flip
            remove_successful = True
        if not remove_successful:
            ErrorPopup(self.master, "Something went wrong during removal! The coin was not deleted.")

    def display_coinlist(self, first_time):
        # this adds a coin to the treeview only if the "displayed" internal value of it is false
        if first_time:
            for c in self.coin_list:
                if c.market == Market.USDT.name:
                    c.market_price = format_dollar(float(c.market_price))
                self.cointree.insert('', 'end',
                                     values=(c.exchange, c.market, c.name, c.market_price, c.usd_price, len(c.alerts)))
        else:
            for c in [x for x in self.coin_list if x.displayed != True]:
                c.displayed = True
                self.cointree.insert('', 'end',
                                     values=(c.exchange, c.market, c.name, c.market_price, c.usd_price, len(c.alerts)))

    def view_alerts(self):
        selected_coin = self.cointree.selection()[0] if len(self.cointree.selection()) > 0 else None
        # if shit in None show a popup
        if selected_coin is None:
            InfoPopup(self.master, "You must select a coin to view alerts!")
            return
        # find coin obj from selected treeview item
        coin_obj = self.find_coin_from_item(selected_coin)
        # make sure shit is there
        if coin_obj is None:
            ErrorPopup(self.master, "Selected coin not found in the internal coin list!")
            return

        self.view_alerts_popup = ViewAlertsPopup(self.master, coin_obj)
        self.view_alerts_button["state"] = "disabled"
        self.master.wait_window(self.view_alerts_popup.top)
        self.view_alerts_button["state"] = "normal"

        ##user might have deleted alerts, so update the alert column
        self.cointree.set(selected_coin, column="alerts", value=len(coin_obj.alerts))

    def find_coin_from_item(self, selection):
        c = next(iter([x for x in self.coin_list if
                       x.name.lower() == self.cointree.item(selection)["values"][2].lower() and x.exchange.lower() ==
                       self.cointree.item(selection)["values"][0].lower() and x.market.lower() ==
                       self.cointree.item(selection)["values"][1].lower()]), None)
        if c is None:
            print("not found!")
            return
        return c

    def find_item_from_coin(self, coin):
        i = next(iter([x for x in self.cointree.get_children() if
                       self.cointree.item(x)["values"][2].lower() == coin.name.lower() and
                       self.cointree.item(x)["values"][0].lower() == coin.exchange.lower() and
                       self.cointree.item(x)["values"][1].lower() == coin.market.lower()]), None)
        if i is None:
            print("not found!")
            return
        return i

    def add_alert(self):
        selected_coin = self.cointree.selection()[0] if len(self.cointree.selection()) > 0 else None
        # if shit in None show a popup
        if selected_coin is None:
            InfoPopup(self.master, "You must select a coin to add an alert!")
            return

        # find coin obj from selected treeview item
        coin_obj = self.find_coin_from_item(selected_coin)

        self.add_alert_popup = AddAlertPopup(self.master, coin_obj)
        self.add_alert_button["state"] = "disabled"
        self.master.wait_window(self.add_alert_popup.top)
        self.add_alert_button["state"] = "normal"

        ##check if user did not fill out form
        if not hasattr(self.add_alert_popup, "value"):
            print("no value 'value' in add_alert_popup")
            return

        alert_data = self.add_alert_popup.value
        # todo:check data for validity
        print(alert_data)

        ##add alert to the coin object if shit is there
        coin_obj.add_alert(
            Alert(
                alert_data[2],
                alert_data[1],
                True if alert_data[0] == 'above' else False
            )
        )
        ##update alert count in the treeview
        self.cointree.set(selected_coin, column="alerts", value=len(coin_obj.alerts))


    def play_notification_sound(self):
        ind = next(iter(
            [i for i in range(len(self.sound_array)) \
             if self.sound_array[i].find(self.settings["sound_name"]) != -1]), None)
        if ind is None:
            ErrorPopup(self.master, "sound " + self.settings["sound_name"] + " not found!")
            return
        playsound(os.path.join(self._SOUNDS, self.sound_array[ind]), block=False)

    def on_closing(self):
        with open("settings.pickle", 'wb') as f:
            pickle.dump(self.settings, f, protocol=pickle.HIGHEST_PROTOCOL)

        with open("coinlist.pickle", 'wb') as f:
            pickle.dump(self.coin_list, f)

        self.rt.stop()
        root.destroy()


my_gui = Overview(root)
# not resizable
root.resizable(0, 0)
root.iconbitmap(ico_)
root.mainloop()
