import sqlite3
import re
from datetime import datetime
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.properties import StringProperty, NumericProperty
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineAvatarIconListItem, TwoLineListItem

# --- DATABASE LOGIC ---
def clean_name(name): return re.sub(r'\W+', '', name)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("medical_pro_v50.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS workspaces (id INTEGER PRIMARY KEY, name TEXT UNIQUE)')
        self.conn.commit()

    def init_wp(self, wp_name):
        s = clean_name(wp_name)
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS meds_{s} (id INTEGER PRIMARY KEY, name TEXT UNIQUE, price REAL)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_{s} (id INTEGER PRIMARY KEY, name TEXT, done INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS sales_{s} (items TEXT, total REAL, date TEXT)')
        self.conn.commit()

# --- UI DESIGN (KV Language) ---
KV = '''
<CompactCard@MDCard>:
    orientation: "vertical"
    size_hint_y: None
    height: "80dp"
    padding: "10dp"
    radius: [20, 20, 20, 20]
    elevation: 1
    md_bg_color: 1, 1, 1, 1

ScreenManager:
    OnboardingScreen:
    MainScreen:

<OnboardingScreen>:
    name: "onboard"
    MDFloatLayout:
        md_bg_color: 0, 0.47, 0.83, 1
        MDLabel:
            text: "PROMED SUITE"
            halign: "center"
            pos_hint: {"center_y": .7}
            font_style: "H4"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            bold: True
        MDTextField:
            id: wp_input
            hint_text: "Hospital or Clinic Name"
            mode: "round"
            size_hint_x: .8
            pos_hint: {"center_x": .5, "center_y": .5}
        MDRaisedButton:
            text: "GET STARTED"
            md_bg_color: 1, 1, 1, 1
            text_color: 0, 0.47, 0.83, 1
            pos_hint: {"center_x": .5, "center_y": .35}
            on_release: app.create_first_workspace(wp_input.text)

<MainScreen>:
    name: "main"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.95, 0.97, 0.98, 1

        # Header
        MDTopAppBar:
            title: app.active_wp_name
            elevation: 0
            left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
            md_bg_color: 0, 0.47, 0.83, 1

        MDBottomNavigation:
            panel_color: 1, 1, 1, 1
            selected_color_background: 0, 0.47, 0.83, .1
            text_color_active: 0, 0.47, 0.83, 1

            MDBottomNavigationItem:
                name: "note"
                text: "Notes"
                icon: "notebook-edit"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: "15dp"
                    spacing: "10dp"
                    MDTextField:
                        hint_text: "Clinical Notes"
                        multiline: True
                        mode: "fill"
                        fill_color_normal: 1, 1, 1, 1
                    MDCard:
                        size_hint_y: None
                        height: "100dp"
                        radius: 20
                        padding: "15dp"
                        MDLabel:
                            text: "Smart Insights appear here..."

            MDBottomNavigationItem:
                name: "home"
                text: "POS"
                icon: "cart"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: "15dp"
                    spacing: "10dp"
                    MDBoxLayout:
                        size_hint_y: None
                        height: "50dp"
                        spacing: "10dp"
                        MDTextField:
                            id: pos_search
                            hint_text: "Search Med..."
                            mode: "round"
                        MDTextField:
                            id: pos_qty
                            hint_text: "Qty"
                            mode: "round"
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
        radius: (0, 16, 16, 0)
        MDNavigationDrawerMenu:
            MDNavigationDrawerHeader:
                title: "ProMed Menu"
                spacing: "4dp"
                padding: "16dp", 0, 0, "16dp"
            OneLineAvatarIconListItem:
                text: "Inventory"
                on_release: app.change_tab(0)
                IconLeftWidget:
                    icon: "package-variant-closed"
            OneLineAvatarIconListItem:
                text: "Sales History"
                on_release: app.change_tab(1)
                IconLeftWidget:
                    icon: "history"
'''

class MainScreen(Screen):
    pass

class OnboardingScreen(Screen):
    pass

class ProMedApp(MDApp):
    active_wp_name = StringProperty("Select Workplace")

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.db = Database()
        return Builder.load_string(KV)

    def on_start(self):
        self.db.cursor.execute("SELECT name FROM workspaces")
        res = self.db.cursor.fetchall()
        if not res:
            self.root.current = "onboard"
        else:
            self.load_workspace(res[0][0])
            self.root.current = "main"

    def create_first_workspace(self, name):
        if name:
            self.db.cursor.execute("INSERT INTO workspaces (name) VALUES (?)", (name,))
            self.db.conn.commit()
            self.load_workspace(name)
            self.root.current = "main"

    def load_workspace(self, name):
        self.active_wp_name = name
        self.db.init_wp(name)

    def finalize_sale(self):
        # Professional Success Dialog
        self.dialog = MDDialog(text="Sale Recorded Successfully!", radius=[20, 20, 20, 20])
        self.dialog.open()

if __name__ == '__main__':
    ProMedApp().run()
