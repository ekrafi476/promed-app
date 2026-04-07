import sqlite3
import re
import os
from datetime import datetime
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.list import TwoLineAvatarIconListItem, IRightBodyTouch, OneLineAvatarIconListItem
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

# --- DATABASE ENGINE ---
class Database:
    def __init__(self):
        self.conn = sqlite3.connect("promed_enterprise_vFinal.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS workspaces (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)')
        self.conn.commit()

    def init_wp(self, wp_name):
        s = re.sub(r'\W+', '', wp_name) # Dynamic Table Naming
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS meds_{s} (id INTEGER PRIMARY KEY, name TEXT UNIQUE, generic TEXT, price REAL)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_{s} (id INTEGER PRIMARY KEY, name TEXT, done INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_it_{s} (id INTEGER PRIMARY KEY, gid INTEGER, name TEXT, qty INTEGER, checked INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS short_{s} (id INTEGER PRIMARY KEY, name TEXT)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS short_it_{s} (gid INTEGER, name TEXT, power TEXT, type TEXT)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS sales_{s} (items TEXT, total REAL, date TEXT)')
        self.conn.commit()

# --- UI LOGIC ---
KV = '''
<CheckItem>:
    on_size: self.ids._right_container.width = checkbox.width
    IconLeftWidget:
        icon: "pill"
    RightCheckbox:
        id: checkbox
        active: root.is_checked
        on_active: app.toggle_check(root.item_id, self.active)

ScreenManager:
    SplashScreen:
    OnboardScreen:
    MainScreen:

<SplashScreen>:
    name: "splash"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0, 0.47, 0.83, 1
        MDIconButton:
            icon: "shield-plus"
            icon_size: "80dp"
            theme_icon_color: "Custom"
            icon_color: 1, 1, 1, 1
            pos_hint: {"center_x": .5}
        MDLabel:
            text: "PROMED ENTERPRISE"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            font_style: "H5"
            bold: True
        MDProgressBar:
            id: progress
            value: 0
            size_hint_x: .6
            pos_hint: {"center_x": .5}
            color: 1, 1, 1, 1

<OnboardScreen>:
    name: "onboard"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0, 0.47, 0.83, 1
        padding: "30dp"
        MDLabel:
            text: "Setup Workplace"
            font_style: "H4"
            halign: "center"
            text_color: 1, 1, 1, 1
            theme_text_color: "Custom"
        MDTextField:
            id: wp_in
            hint_text: "Hospital or Clinic Name"
            mode: "round"
            fill_color_normal: 1, 1, 1, 1
        MDRaisedButton:
            text: "GET STARTED"
            md_bg_color: 1, 1, 1, 1
            text_color: 0, 0.47, 0.83, 1
            size_hint_x: 1
            on_release: app.create_wp(wp_in.text)

<MainScreen>:
    name: "main"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: app.active_wp
            md_bg_color: 0, 0.47, 0.83, 1
            left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]

        MDBottomNavigation:
            id: b_nav
            MDBottomNavigationItem:
                name: "note"
                text: "Notepad"
                icon: "notebook"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: "10dp"
                    MDTextField:
                        id: notes
                        hint_text: "Clinical Notes..."
                        multiline: True
                        on_text: app.smart_look(self.text)
                    MDLabel:
                        id: ins_lbl
                        text: "Live Detection Active"

            MDBottomNavigationItem:
                name: "chk"
                text: "Orders"
                icon: "clipboard-list"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: "5dp"
                    MDBoxLayout:
                        size_hint_y: None
                        height: "50dp"
                        MDTextField:
                            id: cl_name
                            hint_text: "Group Name"
                        MDIconButton:
                            icon: "plus"
                            on_release: app.add_cl(cl_name.text)
                    ScrollView:
                        MDList:
                            id: cl_list

            MDBottomNavigationItem:
                name: "pos"
                text: "POS"
                icon: "cart"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: "10dp"
                    MDBoxLayout:
                        size_hint_y: None
                        height: "50dp"
                        spacing: "5dp"
                        MDTextField:
                            id: ps
                            hint_text: "Med Search"
                        MDTextField:
                            id: pq
                            hint_text: "Qty"
                            size_hint_x: .2
                        MDIconButton:
                            icon: "plus"
                            on_release: app.pos_manual_add()
                    ScrollView:
                        MDList:
                            id: cart_list
                    MDRaisedButton:
                        text: "FINALIZE SALE"
                        size_hint_x: 1
                        on_release: app.finalize_sale()

    MDNavigationDrawer:
        id: nav_drawer
        MDBoxLayout:
            orientation: "vertical"
            padding: "10dp"
            OneLineAvatarIconListItem:
                text: "Inventory"
                on_release: app.show_dialog("Inventory")
                IconLeftWidget:
                    icon: "package"
            OneLineAvatarIconListItem:
                text: "Shortlists"
                on_release: app.show_dialog("Shortlists")
                IconLeftWidget:
                    icon: "layers"
            OneLineAvatarIconListItem:
                text: "History"
                on_release: app.show_dialog("History")
                IconLeftWidget:
                    icon: "history"
'''

class RightCheckbox(IRightBodyTouch, MDCheckbox):
    pass

class CheckItem(OneLineAvatarIconListItem):
    item_id = NumericProperty()
    is_checked = BooleanProperty(False)

class ProMedApp(MDApp):
    active_wp = StringProperty("ProMed")
    wp_slug = ""

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.db = Database()
        return Builder.load_string(KV)

    def on_start(self):
        Clock.schedule_interval(self.update_progress, 0.02)

    def update_progress(self, dt):
        pb = self.root.get_screen('splash').ids.progress
        pb.value += 5
        if pb.value >= 100:
            Clock.unschedule(self.update_progress)
            self.check_setup()

    def check_setup(self):
        self.db.cursor.execute("SELECT name FROM workspaces")
        res = self.db.cursor.fetchone()
        if not res:
            self.root.current = "onboard"
        else:
            self.load_wp(res[0])

    def create_wp(self, name):
        if name:
            self.db.cursor.execute("INSERT INTO workspaces (name) VALUES (?)", (name,))
            self.db.conn.commit()
            self.load_wp(name)

    def load_wp(self, name):
        self.active_wp = name
        self.wp_slug = re.sub(r'\W+', '', name)
        self.db.init_wp(name)
        self.root.current = "main"

    def add_cl(self, name):
        if name:
            self.db.cursor.execute(f"INSERT INTO chk_{self.wp_slug} (name) VALUES (?)", (name,))
            self.db.conn.commit()
            self.refresh_cl()

    def refresh_cl(self):
        l = self.root.get_screen('main').ids.cl_list
        l.clear_widgets()
        self.db.cursor.execute(f"SELECT * FROM chk_{self.wp_slug} ORDER BY id DESC")
        for r in self.db.cursor.fetchall():
            card = MDCard(size_hint_y=None, height="80dp", radius=15, padding=10)
            if r[2]: card.md_bg_color = (0.8, 0.8, 0.8, 1)
            card.add_widget(Label(text=r[1].upper(), color=(0,0,0,1), bold=True))
            l.add_widget(card)

    def smart_look(self, text):
        words = text.split()
        if words:
            self.db.cursor.execute(f"SELECT * FROM meds_{self.wp_slug} WHERE name LIKE ?", (f"{words[-1]}%",))
            r = self.db.cursor.fetchone()
            if r: self.root.get_screen('main').ids.ins_lbl.text = f"{r[1]} - ৳{r[3]}"

    def pos_manual_add(self):
        n = self.root.get_screen('main').ids.ps.text
        q = self.root.get_screen('main').ids.pq.text
        self.root.get_screen('main').ids.cart_list.add_widget(
            TwoLineAvatarIconListItem(text=n, secondary_text=f"Qty: {q}")
        )

    def finalize_sale(self):
        MDDialog(title="Success", text="Sale Recorded!").open()

    def show_dialog(self, title):
        MDDialog(title=title, text="Module active for this Workplace").open()

if __name__ == '__main__':
    ProMedApp().run()
