import sqlite3
import re
import os
from datetime import datetime
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.list import OneLineAvatarIconListItem, TwoLineAvatarIconListItem, IRightBodyTouch, OneLineAvatarListItem
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivymd.uix.filemanager import MDFileManager
from kivy.core.window import Window

# --- DATABASE ENGINE ---
class Database:
    def __init__(self):
        self.conn = sqlite3.connect("promed_enterprise_v10.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS workspaces (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)')
        self.conn.commit()

    def clean_name(self, name):
        return re.sub(r'\W+', '', name)

    def init_wp(self, wp_name):
        s = self.clean_name(wp_name)
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS med_{s} (id INTEGER PRIMARY KEY, name TEXT UNIQUE, gen TEXT, co TEXT, cat TEXT, price REAL, img TEXT)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_{s} (id INTEGER PRIMARY KEY, name TEXT, done INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_it_{s} (id INTEGER PRIMARY KEY, gid INTEGER, name TEXT, qty INTEGER, checked INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS short_{s} (id INTEGER PRIMARY KEY, name TEXT)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS short_it_{s} (id INTEGER PRIMARY KEY, gid INTEGER, name TEXT, pwr TEXT, type TEXT)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS sales_{s} (items TEXT, total REAL, date TEXT)')
        self.conn.commit()

# --- UI DESIGN (KV) ---
KV = '''
<CheckItem>:
    IconLeftWidget:
        icon: "pill"
    RightCheckbox:
        active: root.is_checked
        on_active: app.toggle_chk_item(root.item_id, self.active)

ScreenManager:
    SplashScreen:
    OnboardScreen:
    MainScreen:

<SplashScreen>:
    name: "splash"
    MDFloatLayout:
        md_bg_color: 0, 0.47, 0.83, 1
        MDIconButton:
            icon: "heart-pulse"
            icon_size: "80dp"
            theme_icon_color: "Custom"
            icon_color: 1, 1, 1, 1
            pos_hint: {"center_x": .5, "center_y": .6}
        MDLabel:
            text: "PROMED ENTERPRISE"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            font_style: "H5"
            bold: True
            pos_hint: {"center_y": .45}
        MDProgressBar:
            id: progress
            value: 0
            max: 100
            size_hint_x: .6
            pos_hint: {"center_x": .5, "center_y": .3}
            color: 1, 1, 1, 1

<OnboardScreen>:
    name: "onboard"
    MDFloatLayout:
        md_bg_color: 0, 0.47, 0.83, 1
        MDLabel:
            text: "Welcome to ProMed"
            font_style: "H4"
            halign: "center"
            pos_hint: {"center_y": .7}
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
        MDTextField:
            id: wp_in
            hint_text: "Workplace Name (Clinic/Hospital)"
            mode: "round"
            size_hint_x: .8
            pos_hint: {"center_x": .5, "center_y": .5}
        MDRaisedButton:
            text: "GET STARTED"
            md_bg_color: 1, 1, 1, 1
            text_color: 0, 0.47, 0.83, 1
            pos_hint: {"center_x": .5, "center_y": .35}
            on_release: app.create_wp(wp_in.text)

<MainScreen>:
    name: "main"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: app.active_wp_name
            elevation: 2
            md_bg_color: 0, 0.47, 0.83, 1
            left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
            right_action_items: [["swap-horizontal", lambda x: app.show_wp_switcher()]]

        MDBottomNavigation:
            id: b_nav
            MDBottomNavigationItem:
                name: "note"
                text: "Notepad"
                icon: "notebook-edit"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: "15dp"
                    MDTextField:
                        id: note_in
                        hint_text: "Clinical Notes..."
                        multiline: True
                        on_text: app.smart_lookup(self.text)
                    MDCard:
                        size_hint_y: None
                        height: "100dp"
                        radius: 20
                        padding: "10dp"
                        MDLabel:
                            id: insight_lbl
                            text: "Type med name for lookup..."

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
                            id: cl_name
                            hint_text: "New Group"
                        MDIconButton:
                            icon: "plus-circle"
                            on_release: app.add_chk_group(cl_name.text)
                    ScrollView:
                        MDList:
                            id: cl_container

            MDBottomNavigationItem:
                name: "pos"
                text: "POS"
                icon: "calculator"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: "10dp"
                    MDBoxLayout:
                        size_hint_y: None
                        height: "50dp"
                        spacing: "5dp"
                        MDTextField:
                            id: pos_search
                            hint_text: "Search med..."
                        MDTextField:
                            id: pos_qty
                            hint_text: "Qty"
                            size_hint_x: .3
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

            MDBottomNavigationItem:
                name: "inv"
                text: "Inventory"
                icon: "package-variant"
                MDBoxLayout:
                    orientation: "vertical"
                    MDRaisedButton:
                        text: "ADD PRODUCT"
                        size_hint_x: 1
                        on_release: app.open_inv_dialog()
                    ScrollView:
                        MDList:
                            id: inv_container

    MDNavigationDrawer:
        id: nav_drawer
        radius: (0, 16, 16, 0)
        MDBoxLayout:
            orientation: "vertical"
            padding: "10dp"
            MDLabel:
                text: "Clinical Tools"
                font_style: "H6"
                size_hint_y: None
                height: "50dp"
            OneLineAvatarListItem:
                text: "Shortlists"
                on_release: app.open_shortlists()
                IconLeftWidget:
                    icon: "layers-triple"
            OneLineAvatarListItem:
                text: "History"
                on_release: app.open_history()
                IconLeftWidget:
                    icon: "history"
            Widget:
'''

class RightCheckbox(IRightBodyTouch, MDCheckbox):
    pass

class CheckItem(TwoLineAvatarIconListItem):
    item_id = NumericProperty()
    is_checked = NumericProperty()

class ProMedApp(MDApp):
    active_wp_name = StringProperty("ProMed")
    active_wp_slug = StringProperty("")

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.db = Database()
        return Builder.load_string(KV)

    def on_start(self):
        Clock.schedule_interval(self.update_splash, 0.03)

    def update_splash(self, dt):
        pb = self.root.get_screen('splash').ids.progress
        if pb.value < 100:
            pb.value += 2
        else:
            Clock.unschedule(self.update_splash)
            self.check_setup()

    def check_setup(self):
        self.db.cursor.execute("SELECT name FROM workspaces")
        res = self.db.cursor.fetchall()
        if not res:
            self.root.current = "onboard"
        else:
            self.load_wp(res[0][0])
            self.root.current = "main"

    def create_wp(self, name):
        if name:
            self.db.cursor.execute("INSERT INTO workspaces (name) VALUES (?)", (name,))
            self.db.conn.commit()
            self.load_wp(name)
            self.root.current = "main"

    def load_wp(self, name):
        self.active_wp_name = name
        self.active_wp_slug = self.db.clean_name(name)
        self.db.init_wp(name)
        self.refresh_all()

    def refresh_all(self):
        self.refresh_cl()
        self.refresh_inv()

    # --- INVENTORY ---
    def open_inv_dialog(self):
        # Professional Popup for Registration
        self.dialog = MDDialog(
            title="Register Product",
            type="custom",
            content_cls=MDBoxLayout(orientation='vertical', adaptive_height=True, spacing="10dp"),
            buttons=[MDRaisedButton(text="SAVE", on_release=self.save_inv)]
        )
        self.dialog.content_cls.add_widget(QLineEdit(placeholder_text="Name", id="n"))
        self.dialog.content_cls.add_widget(QLineEdit(placeholder_text="Price", id="p"))
        self.dialog.open()

    def save_inv(self, *args):
        # Logic to save and refresh
        self.dialog.dismiss()
        self.refresh_inv()

    def refresh_inv(self):
        container = self.root.get_screen('main').ids.inv_container
        container.clear_widgets()
        self.db.cursor.execute(f"SELECT * FROM med_{self.active_wp_slug}")
        for r in self.db.cursor.fetchall():
            container.add_widget(TwoLineAvatarIconListItem(text=r[1], secondary_text=f"৳{r[5]}"))

    # --- CHECKLIST ---
    def add_chk_group(self, name):
        if name:
            self.db.cursor.execute(f"INSERT INTO chk_{self.active_wp_slug} (name) VALUES (?)", (name,))
            self.db.conn.commit()
            self.refresh_cl()

    def refresh_cl(self):
        container = self.root.get_screen('main').ids.cl_container
        container.clear_widgets()
        self.db.cursor.execute(f"SELECT * FROM chk_{self.active_wp_slug} ORDER BY id DESC")
        for row in self.db.cursor.fetchall():
            card = MDCard(orientation='vertical', size_hint_y=None, height="120dp", radius=20, padding=10)
            if row[2]: card.md_bg_color = (0.9, 0.9, 0.9, 1)
            card.add_widget(QLabel(text=row[1].upper(), color=(0,0,0,1), bold=True))
            container.add_widget(card)

    def finalize_sale(self):
        MDDialog(text="Payment Recorded!").open()

    def smart_lookup(self, text):
        words = text.split()
        if words:
            self.db.cursor.execute(f"SELECT * FROM med_{self.active_wp_slug} WHERE name LIKE ?", (f"{words[-1]}%",))
            r = self.db.cursor.fetchone()
            if r: self.root.get_screen('main').ids.insight_lbl.text = f"{r[1]} - ৳{r[5]}"

if __name__ == '__main__':
    ProMedApp().run()
