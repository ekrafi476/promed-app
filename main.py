import os
import sqlite3
import re
from datetime import datetime
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.core.window import Window

from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.list import TwoLineAvatarIconListItem, OneLineAvatarIconListItem, MDList, IRightBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.textfield import MDTextField
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS workspaces (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)')
        self.conn.commit()

    def get_slug(self, name):
        return re.sub(r'\W+', '', name.lower())

    def init_wp(self, wp_name):
        s = self.get_slug(wp_name)
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS meds_{s} (id INTEGER PRIMARY KEY, name TEXT UNIQUE, gen TEXT, price REAL)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_{s} (id INTEGER PRIMARY KEY, name TEXT, done INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_it_{s} (id INTEGER PRIMARY KEY, gid INTEGER, name TEXT, qty INTEGER, checked INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS short_{s} (id INTEGER PRIMARY KEY, name TEXT)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS short_it_{s} (gid INTEGER, name TEXT, pwr TEXT, type TEXT)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS sales_{s} (items TEXT, total REAL, date TEXT)')
        self.conn.commit()

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
            text: "PROMED Beta v1.0.3"
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
        padding: "40dp"
        spacing: "20dp"
        MDLabel:
            text: "Workspace Setup"
            font_style: "H4"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
        MDTextField:
            id: wp_name
            hint_text: "Clinic or Hospital Name"
            mode: "round"
            fill_color_normal: 1, 1, 1, 1
        MDRaisedButton:
            text: "LAUNCH SYSTEM"
            md_bg_color: 1, 1, 1, 1
            text_color: 0, 0.47, 0.83, 1
            size_hint_x: 1
            on_release: app.create_workspace(wp_name.text)

<MainScreen>:
    name: "main"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.95, 0.96, 0.98, 1

        MDTopAppBar:
            title: app.active_wp_display
            elevation: 2
            md_bg_color: 0, 0.47, 0.83, 1
            left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]

        MDBottomNavigation:
            id: bottom_nav
            panel_color: 1, 1, 1, 1

            MDBottomNavigationItem:
                name: "note"
                text: "Notepad"
                icon: "notebook-edit"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: "15dp"
                    MDTextField:
                        id: clin_note
                        hint_text: "Consultation Notes..."
                        multiline: True
                        on_text: app.detect_med(self.text)
                    MDCard:
                        size_hint_y: None
                        height: "110dp"
                        radius: 25
                        padding: "15dp"
                        MDLabel:
                            id: insight_lbl
                            text: "Smart Aero Insight"
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
                            id: cl_name
                            hint_text: "Add Group..."
                        MDIconButton:
                            icon: "plus-circle"
                            on_release: app.add_cl_group(cl_name.text)
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
                            id: ps_search
                            hint_text: "Medicine Name"
                        MDTextField:
                            id: ps_qty
                            hint_text: "Qty"
                            size_hint_x: .2
                            text: "1"
                        MDIconButton:
                            icon: "cart-plus"
                            on_release: app.pos_add_item()
                    ScrollView:
                        MDList:
                            id: pos_cart
                    MDRaisedButton:
                        text: "FINALIZE TRANSACTION"
                        size_hint_x: 1
                        on_release: app.finalize_sale()

    MDNavigationDrawer:
        id: nav_drawer
        radius: (0, 25, 25, 0)
        MDBoxLayout:
            orientation: "vertical"
            padding: "15dp"
            spacing: "10dp"
            MDLabel:
                text: "System Explorer"
                font_style: "Button"
            OneLineAvatarIconListItem:
                text: "Inventory Management"
                on_release: app.nav_to("inventory")
                IconLeftWidget:
                    icon: "package-variant-closed"
            OneLineAvatarIconListItem:
                text: "Clinical History"
                on_release: app.nav_to("history")
                IconLeftWidget:
                    icon: "history"
            Widget:

<InventoryScreen>:
    name: "inventory"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Inventory"
            left_action_items: [["arrow-left", lambda x: app.back_home()]]
        MDRaisedButton:
            text: "REGISTER PRODUCT"
            size_hint_x: 1
            on_release: app.open_inv_dialog()
        ScrollView:
            MDList:
                id: inv_list

<HistoryScreen>:
    name: "history"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Logs"
            left_action_items: [["arrow-left", lambda x: app.back_home()]]
        ScrollView:
            MDList:
                id: hist_list
'''

class ProMedApp(MDApp):
    active_wp_display = StringProperty("ProMed")
    wp_slug = ""

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.sm = ScreenManager(transition=SlideTransition())
        self.sm.add_widget(Builder.load_string(KV))
        self.sm.add_widget(InventoryScreen(name="inventory"))
        self.sm.add_widget(HistoryScreen(name="history"))
        return self.sm

    def on_start(self):
        db_path = os.path.join(self.user_data_dir, "promed_v103.db")
        self.db = Database(db_path)
        Clock.schedule_interval(self.update_splash, 0.03)

    def update_splash(self, dt):
        pb = self.sm.get_screen('splash').ids.progress
        pb.value += 5
        if pb.value >= 100:
            Clock.unschedule(self.update_splash)
            self.check_setup()

    def check_setup(self):
        self.db.cursor.execute("SELECT name FROM workspaces")
        res = self.db.cursor.fetchone()
        if not res: self.sm.current = "onboard"
        else: self.load_workspace(res[0])

    def create_workspace(self, name):
        if name:
            self.db.cursor.execute("INSERT INTO workspaces (name) VALUES (?)", (name,))
            self.db.conn.commit(); self.load_workspace(name)

    def load_workspace(self, name):
        self.active_wp_display = name
        self.wp_slug = self.db.get_slug(name)
        self.db.init_wp(name)
        self.sm.current = "main"
        self.refresh_all()

    def refresh_all(self):
        self.refresh_inv(); self.refresh_cl()

    def open_inv_dialog(self):
        self.dialog = MDDialog(
            title="Add Product", type="custom",
            content_cls=MDBoxLayout(orientation="vertical", adaptive_height=True, spacing="10dp"),
            buttons=[MDRaisedButton(text="SAVE", on_release=self.save_inv)]
        )
        self.dialog.content_cls.add_widget(MDTextField(hint_text="Med Name"))
        self.dialog.content_cls.add_widget(MDTextField(hint_text="Price"))
        self.dialog.open()

    def save_inv(self, *args):
        inputs = self.dialog.content_cls.children
        name, price = inputs[1].text, inputs[0].text
        if name and price:
            self.db.cursor.execute(f"INSERT INTO meds_{self.wp_slug} (name, price) VALUES (?,?)", (name, float(price)))
            self.db.conn.commit(); self.refresh_inv(); self.dialog.dismiss()

    def refresh_inv(self):
        l = self.sm.get_screen('inventory').ids.inv_list; l.clear_widgets()
        self.db.cursor.execute(f"SELECT * FROM meds_{self.wp_slug}")
        for r in self.db.cursor.fetchall(): l.add_widget(OneLineAvatarIconListItem(text=f"{r[1]} - ৳{r[3]}"))

    def add_cl_group(self, name):
        if name: self.db.cursor.execute(f"INSERT INTO chk_{self.wp_slug} (name) VALUES (?)", (name,)); self.db.conn.commit(); self.refresh_cl()

    def refresh_cl(self):
        c = self.sm.get_screen('main').ids.cl_container; c.clear_widgets()
        self.db.cursor.execute(f"SELECT * FROM chk_{self.wp_slug} ORDER BY id DESC")
        for r in self.db.cursor.fetchall():
            card = MDCard(size_hint_y=None, height="60dp", radius=15, padding=10)
            card.add_widget(MDLabel(text=r[1].upper(), bold=True))
            c.add_widget(card)

    def pos_add_item(self):
        n = self.sm.get_screen('main').ids.pos_search.text
        q = int(self.sm.get_screen('main').ids.pos_qty.text or 1)
        self.db.cursor.execute(f"SELECT price FROM meds_{self.wp_slug} WHERE name=?", (n,))
        r = self.db.cursor.fetchone()
        if r:
            self.sm.get_screen('main').ids.pos_cart.add_widget(OneLineAvatarIconListItem(text=f"{n} x{q} = ৳{r[0]*q}"))

    def finalize_sale(self): MDDialog(title="Paid", text="Transaction Recorded").open()
    def detect_med(self, t): pass
    def nav_to(self, s): self.sm.current = s; self.sm.get_screen('main').ids.nav_drawer.set_state("close")
    def back_home(self): self.sm.current = "main"

class InventoryScreen(Screen): pass
class HistoryScreen(Screen): pass

if __name__ == '__main__':
    ProMedApp().run()
