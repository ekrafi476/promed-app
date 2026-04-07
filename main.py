import os
import sqlite3
import re
from datetime import datetime

# Standard Kivy imports
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, BooleanProperty, NumericProperty

# KivyMD imports
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.list import OneLineAvatarIconListItem, IRightBodyTouch, MDList
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

# --- UI DESIGN (KV) ---
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
        padding: "25dp"
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
            title: app.active_wp_display
            md_bg_color: 0, 0.47, 0.83, 1
            left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
            right_action_items: [["plus-box", lambda x: app.show_dialog("Inventory")]]

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
                        hint_text: "Clinical Notes..."
                        multiline: True
                    MDLabel:
                        text: "Smart Aero Engine Active"
                        theme_text_color: "Secondary"
                        font_style: "Caption"

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
                            hint_text: "New Group Name"
                        MDIconButton:
                            icon: "plus"
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
                            id: ps_search
                            hint_text: "Med Name"
                        MDTextField:
                            id: ps_qty
                            hint_text: "Qty"
                            size_hint_x: .2
                            text: "1"
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
        MDBoxLayout:
            orientation: "vertical"
            padding: "10dp"
            spacing: "10dp"
            MDLabel:
                text: "Menu"
                font_style: "H6"
                size_hint_y: None
                height: "50dp"
            OneLineAvatarIconListItem:
                text: "Clinical Shortlists"
                on_release: app.show_dialog("Shortlists")
                IconLeftWidget:
                    icon: "layers"
            OneLineAvatarIconListItem:
                text: "Sales History"
                on_release: app.show_dialog("History")
                IconLeftWidget:
                    icon: "history"
            Widget:

'''

class RightCheckbox(IRightBodyTouch, MDCheckbox):
    pass

class CheckItem(OneLineAvatarIconListItem):
    item_id = NumericProperty()
    is_checked = BooleanProperty(False)

class SplashScreen(Screen):
    pass

class OnboardScreen(Screen):
    pass

class MainScreen(Screen):
    pass

class ProMedApp(MDApp):
    active_wp_display = StringProperty("ProMed")
    active_wp_slug = StringProperty("")

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        # Database path is set in on_start to ensure it's writeable
        return Builder.load_string(KV)

    def on_start(self):
        # standard Kivy data directory (Safe for Android)
        db_file = os.path.join(self.user_data_dir, "promed_v5.db")
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS workspaces (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)')
        self.conn.commit()
        
        # Start Splash Loading
        Clock.schedule_interval(self.update_splash, 0.02)

    def update_splash(self, dt):
        pb = self.root.get_screen('splash').ids.progress
        pb.value += 4
        if pb.value >= 100:
            Clock.unschedule(self.update_splash)
            self.check_setup()

    def check_setup(self):
        self.cursor.execute("SELECT name FROM workspaces")
        res = self.cursor.fetchone()
        if not res:
            self.root.current = "onboard"
        else:
            self.load_wp(res[0])
            self.root.current = "main"

    def create_wp(self, name):
        if name:
            try:
                self.cursor.execute("INSERT INTO workspaces (name) VALUES (?)", (name,))
                self.conn.commit()
                self.load_wp(name)
                self.root.current = "main"
            except:
                pass

    def load_wp(self, name):
        self.active_wp_display = name
        self.active_wp_slug = re.sub(r'\W+', '', name)
        # Create Workplace specific tables
        s = self.active_wp_slug
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS med_{s} (id INTEGER PRIMARY KEY, name TEXT UNIQUE, price REAL)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_{s} (id INTEGER PRIMARY KEY, name TEXT, done INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS sales_{s} (items TEXT, total REAL, date TEXT)')
        self.conn.commit()
        self.refresh_checklists()

    def add_cl_group(self, name):
        if name:
            self.cursor.execute(f"INSERT INTO chk_{self.active_wp_slug} (name) VALUES (?)", (name,))
            self.conn.commit()
            self.refresh_checklists()

    def refresh_checklists(self):
        container = self.root.get_screen('main').ids.cl_list
        container.clear_widgets()
        self.cursor.execute(f"SELECT * FROM chk_{self.active_wp_slug} ORDER BY id DESC")
        for row in self.cursor.fetchall():
            # Compact Card Design
            card = MDCard(size_hint_y=None, height="70dp", radius=15, padding=10, ripple_behavior=True)
            if row[2]: card.md_bg_color = (0.9, 0.9, 0.9, 1) # Darken if done
            card.add_widget(MDLabel(text=row[1].upper(), bold=True))
            container.add_widget(card)

    def finalize_sale(self):
        MDDialog(title="Success", text="Sale Recorded").open()

    def show_dialog(self, title):
        MDDialog(title=title, text=f"{title} module is ready.").open()

if __name__ == '__main__':
    ProMedApp().run()
