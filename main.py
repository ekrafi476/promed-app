import sqlite3
import re
from datetime import datetime
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.list import OneLineAvatarIconListItem, TwoLineListItem, IRightBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.label import Label

# --- DATABASE ---
class Database:
    def __init__(self):
        self.conn = sqlite3.connect("med_quantum_v9.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS workspaces (id INTEGER PRIMARY KEY, name TEXT UNIQUE)')
        self.conn.commit()

    def init_wp(self, wp_name):
        s = re.sub(r'\W+', '', wp_name)
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS meds_{s} (id INTEGER PRIMARY KEY, name TEXT UNIQUE, gen TEXT, price REAL)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_{s} (id INTEGER PRIMARY KEY, name TEXT, done INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_it_{s} (id INTEGER PRIMARY KEY, gid INTEGER, name TEXT, qty INTEGER, checked INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS sales_{s} (items TEXT, total REAL, date TEXT)')
        self.conn.commit()

# --- UI DESIGN ---
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
        spacing: "20dp"
        MDIconButton:
            icon: "shield-plus"
            icon_size: "100dp"
            theme_icon_color: "Custom"
            icon_color: 1, 1, 1, 1
            pos_hint: {"center_x": .5}
        MDLabel:
            text: "PROMED QUANTUM"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            font_style: "H4"
            bold: True
        MDProgressBar:
            id: progress
            value: 0
            size_hint_x: .8
            pos_hint: {"center_x": .5}
            color: 1, 1, 1, 1

<OnboardScreen>:
    name: "onboard"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0, 0.47, 0.83, 1
        padding: "30dp"
        spacing: "20dp"
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
            on_release: app.create_workspace(wp_in.text)

<MainScreen>:
    name: "main"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: app.active_wp
            md_bg_color: 0, 0.47, 0.83, 1
            left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
            right_action_items: [["plus", lambda x: app.open_inventory()]]

        MDBottomNavigation:
            MDBottomNavigationItem:
                name: "note"
                text: "Notepad"
                icon: "notebook"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: "15dp"
                    MDTextField:
                        id: notes
                        hint_text: "Clinical Notes"
                        multiline: True
                    MDCard:
                        size_hint_y: None
                        height: "80dp"
                        radius: 20
                        padding: "15dp"
                        MDLabel:
                            text: "Smart math active..."

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
                            id: pos_search
                            hint_text: "Search med..."
                        MDTextField:
                            id: pos_qty
                            hint_text: "Qty"
                            size_hint_x: .3
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
                text: "Switch Workspace"
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
        pb.value += 2
        if pb.value >= 100:
            Clock.unschedule(self.update_splash)
            self.check_setup()

    def check_setup(self):
        self.db.cursor.execute("SELECT name FROM workspaces")
        res = self.db.cursor.fetchone()
        if not res:
            self.root.current = "onboard"
        else:
            self.load_workspace(res[0])

    def create_workspace(self, name):
        if name:
            self.db.cursor.execute("INSERT INTO workspaces (name) VALUES (?)", (name,))
            self.db.conn.commit()
            self.load_workspace(name)

    def load_workspace(self, name):
        self.active_wp = name
        self.wp_slug = re.sub(r'\W+', '', name)
        self.db.init_wp(name)
        self.root.current = "main"

    def finalize_sale(self):
        MDDialog(title="Success", text="Sale Completed").open()

    def open_inventory(self):
        # Professional Popup
        MDDialog(title="Add Med", text="Inventory Entry").open()

if __name__ == '__main__':
    ProMedApp().run()
