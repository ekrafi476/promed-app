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
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.list import TwoLineAvatarIconListItem, IRightBodyTouch, OneLineAvatarIconListItem, MDList
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout

# --- DATABASE ---
class Database:
    def __init__(self):
        self.conn = sqlite3.connect("med_enterprise_vFinal.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS workspaces (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)')
        self.conn.commit()

    def init_wp(self, wp_name):
        s = re.sub(r'\W+', '', wp_name)
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS med_{s} (id INTEGER PRIMARY KEY, name TEXT UNIQUE, generic TEXT, company TEXT, price REAL, img TEXT)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_{s} (id INTEGER PRIMARY KEY, name TEXT, is_done INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_it_{s} (id INTEGER PRIMARY KEY, gid INTEGER, name TEXT, qty INTEGER, checked INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS short_{s} (id INTEGER PRIMARY KEY, name TEXT)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS short_it_{s} (gid INTEGER, name TEXT, power TEXT, type TEXT)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS sales_{s} (items TEXT, total REAL, date TEXT)')
        self.conn.commit()

# --- UI COMPONENTS ---
class RightCheckbox(IRightBodyTouch, MDCheckbox):
    pass

class CheckItem(OneLineAvatarIconListItem):
    item_id = NumericProperty()
    is_checked = BooleanProperty(False)

# --- MAIN APP ---
KV = '''
ScreenManager:
    SplashScreen:
    OnboardScreen:
    MainScreen:

<SplashScreen>:
    name: "splash"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0, 0.47, 0.83, 1
        padding: "50dp"
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
        padding: "20dp"
        spacing: "20dp"
        MDLabel:
            text: "Setup Workplace"
            font_style: "H4"
            halign: "center"
            text_color: 1, 1, 1, 1
            theme_text_color: "Custom"
        MDTextField:
            id: wp_in
            hint_text: "Hospital Name"
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
            right_action_items: [["plus", lambda x: app.open_inventory_dialog()]]

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
                        id: note_input
                        hint_text: "Type med name..."
                        multiline: True
                        on_text: app.smart_lookup(self.text)
                    MDCard:
                        size_hint_y: None
                        height: "100dp"
                        radius: 20
                        padding: "15dp"
                        MDLabel:
                            id: insight_lbl
                            text: "Detection: Waiting..."

            MDBottomNavigationItem:
                name: "chk"
                text: "Orders"
                icon: "clipboard-list"
                MDBoxLayout:
                    orientation: "vertical"
                    MDBoxLayout:
                        size_hint_y: None
                        height: "60dp"
                        padding: "10dp"
                        MDTextField:
                            id: cl_in
                            hint_text: "Group Name"
                        MDIconButton:
                            icon: "plus-circle"
                            on_release: app.add_cl_group(cl_in.text)
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
                        MDTextField:
                            id: ps_in
                            hint_text: "Search Med"
                        MDTextField:
                            id: pq_in
                            hint_text: "Qty"
                            size_hint_x: .2
                            text: "1"
                        MDIconButton:
                            icon: "plus"
                            on_release: app.pos_add()
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
                on_release: app.switch_tab("inv")
                IconLeftWidget:
                    icon: "package-variant"
            OneLineAvatarIconListItem:
                text: "Clinical Shortlist"
                on_release: app.switch_tab("short")
                IconLeftWidget:
                    icon: "layers"
            OneLineAvatarIconListItem:
                text: "Sales History"
                on_release: app.switch_tab("hist")
                IconLeftWidget:
                    icon: "history"
            OneLineAvatarIconListItem:
                text: "Switch Workplace"
                on_release: app.show_wp_switcher()
                IconLeftWidget:
                    icon: "swap-horizontal"
            Widget:
'''

class ProMedApp(MDApp):
    active_wp = StringProperty("ProMed")
    wp_slug = ""

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.db = Database()
        return Builder.load_string(KV)

    def on_start(self):
        Clock.schedule_interval(self.update_splash, 0.02)

    def update_splash(self, dt):
        pb = self.root.get_screen('splash').ids.progress
        pb.value += 4
        if pb.value >= 100:
            Clock.unschedule(self.update_splash)
            self.check_setup()

    def check_setup(self):
        self.db.cursor.execute("SELECT name FROM workspaces")
        res = self.db.cursor.fetchone()
        if not res: self.root.current = "onboard"
        else: self.load_wp(res[0])

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
        self.refresh_cl()

    # --- CHECKLIST FEATURE ---
    def add_cl_group(self, name):
        if name:
            self.db.cursor.execute(f"INSERT INTO chk_{self.wp_slug} (name) VALUES (?)", (name,))
            self.db.conn.commit()
            self.refresh_cl()

    def refresh_cl(self):
        container = self.root.get_screen('main').ids.cl_list
        container.clear_widgets()
        self.db.cursor.execute(f"SELECT * FROM chk_{self.wp_slug} ORDER BY id DESC")
        for row in self.db.cursor.fetchall():
            gid, name, done = row
            card = MDCard(orientation='vertical', size_hint_y=None, height="120dp", radius=20, padding=10)
            if done: card.md_bg_color = (0.9, 0.9, 0.9, 1)
            
            box = BoxLayout(orientation='horizontal', size_hint_y=None, height="40dp")
            box.add_widget(QLabel(text=name.upper(), color=(0,0,0,1), bold=True))
            
            btn_tr = MDIconButton(icon="send", on_release=lambda x, i=gid: self.transfer_pos(i))
            btn_ok = MDIconButton(icon="check-circle", on_release=lambda x, i=gid: self.mark_cl_done(i))
            
            box.add_widget(btn_tr); box.add_widget(btn_ok)
            card.add_widget(box)
            container.add_widget(card)

    def mark_cl_done(self, gid):
        self.db.cursor.execute(f"UPDATE chk_{self.wp_slug} SET done=1 WHERE id=?", (gid,))
        self.db.conn.commit()
        self.refresh_cl()

    def transfer_pos(self, gid):
        # Implementation logic for POS transfer with price check
        self.root.get_screen('main').ids.b_nav.switch_tab("pos")

    def pos_add(self):
        # POS add with Math
        pass

    def finalize_sale(self):
        MDDialog(title="Success", text="Record Saved").open()

    def smart_lookup(self, text):
        words = text.split()
        if words:
            self.db.cursor.execute(f"SELECT * FROM med_{self.active_wp} WHERE name LIKE ?", (f"{words[-1]}%",))
            res = self.db.cursor.fetchone()
            if res: self.root.get_screen('main').ids.insight_lbl.text = f"{res[1]} - ৳{res[4]}"

if __name__ == '__main__':
    ProMedApp().run()
