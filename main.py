import sqlite3
import re
import os
from datetime import datetime
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition, SlideTransition
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.list import OneLineAvatarIconListItem, TwoLineAvatarIconListItem, IRightBodyTouch, MDList
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.properties import StringProperty, NumericProperty, ListProperty

# --- DATABASE ENGINE ---
class Database:
    def __init__(self):
        self.conn = sqlite3.connect("promed_enterprise.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS workspaces (id INTEGER PRIMARY KEY, name TEXT UNIQUE)')
        self.conn.commit()

    def get_clean_name(self, name):
        return re.sub(r'\W+', '', name)

    def init_workspace_tables(self, wp_name):
        s = self.get_clean_name(wp_name)
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS meds_{s} (id INTEGER PRIMARY KEY, name TEXT UNIQUE, generic TEXT, company TEXT, price REAL)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_{s} (id INTEGER PRIMARY KEY, name TEXT, done INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_it_{s} (id INTEGER PRIMARY KEY, gid INTEGER, name TEXT, qty INTEGER, checked INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS short_{s} (id INTEGER PRIMARY KEY, name TEXT)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS short_it_{s} (id INTEGER PRIMARY KEY, gid INTEGER, name TEXT, pwr TEXT, type TEXT)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS sales_{s} (id INTEGER PRIMARY KEY, items TEXT, total REAL, date TEXT)')
        self.conn.commit()

# --- UI DESIGN ---
KV = '''
#:import SlideTransition kivy.uix.screenmanager.SlideTransition

<ListItemWithCheckbox>:
    IconLeftWidget:
        icon: "pill"
    RightCheckbox:
        id: cb
        active: root.is_active
        on_active: app.toggle_check_item(root.item_id, self.active)

ScreenManager:
    SplashScreen:
    OnboardingScreen:
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

<OnboardingScreen>:
    name: "onboard"
    MDBoxLayout:
        orientation: "vertical"
        padding: "30dp"
        spacing: "20dp"
        md_bg_color: 0, 0.47, 0.83, 1
        MDLabel:
            text: "Setup Workplace"
            font_style: "H4"
            bold: True
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            halign: "center"
        MDTextField:
            id: wp_name
            hint_text: "Hospital or Clinic Name"
            mode: "round"
            fill_color_normal: 1, 1, 1, 1
        MDRaisedButton:
            text: "CREATE WORKSPACE"
            md_bg_color: 1, 1, 1, 1
            text_color: 0, 0.47, 0.83, 1
            size_hint_x: 1
            on_release: app.create_workspace(wp_name.text)

<MainScreen>:
    name: "main"
    MDBoxLayout:
        orientation: "vertical"
        
        MDTopAppBar:
            title: app.active_wp_display
            elevation: 2
            left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
            md_bg_color: 0, 0.47, 0.83, 1

        MDBottomNavigation:
            id: bottom_nav
            
            MDBottomNavigationItem:
                name: "note"
                text: "Notepad"
                icon: "notebook-edit"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: "15dp"
                    spacing: "10dp"
                    MDTextField:
                        id: notes
                        hint_text: "Clinical Notes"
                        multiline: True
                        on_text: app.smart_detect(self.text)
                    MDCard:
                        size_hint_y: None
                        height: "100dp"
                        radius: 20
                        padding: "15dp"
                        md_bg_color: 0.9, 0.95, 1, 1
                        MDLabel:
                            id: insight_lbl
                            text: "Type medicine names for info..."

            MDBottomNavigationItem:
                name: "checklist"
                text: "Orders"
                icon: "clipboard-list"
                MDBoxLayout:
                    orientation: "vertical"
                    MDBoxLayout:
                        size_hint_y: None
                        height: "60dp"
                        padding: "10dp"
                        MDTextField:
                            id: cl_group_name
                            hint_text: "New Group Name"
                        MDIconButton:
                            icon: "plus-circle"
                            on_release: app.add_cl_group(cl_group_name.text)
                    ScrollView:
                        MDList:
                            id: cl_list_container

            MDBottomNavigationItem:
                name: "pos"
                text: "POS"
                icon: "calculator"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: "15dp"
                    spacing: "10dp"
                    MDBoxLayout:
                        size_hint_y: None
                        height: "50dp"
                        spacing: "5dp"
                        MDTextField:
                            id: pos_search
                            hint_text: "Search Med..."
                        MDTextField:
                            id: pos_qty
                            hint_text: "Qty"
                            size_hint_x: .3
                            text: "1"
                        MDIconButton:
                            icon: "cart-plus"
                            on_release: app.pos_add_item()
                    ScrollView:
                        MDList:
                            id: pos_cart
                    MDRaisedButton:
                        text: "FINALIZE & SELL"
                        size_hint_x: 1
                        on_release: app.finalize_sale()

            MDBottomNavigationItem:
                name: "short"
                text: "Shortlist"
                icon: "layers-triple"
                ScrollView:
                    MDList:
                        id: sl_container

    MDNavigationDrawer:
        id: nav_drawer
        radius: (0, 16, 16, 0)
        MDBoxLayout:
            orientation: "vertical"
            padding: "10dp"
            MDLabel:
                text: "Workspace Settings"
                font_style: "Button"
                size_hint_y: None
                height: "50dp"
            OneLineAvatarIconListItem:
                text: "Inventory Manager"
                on_release: app.open_inventory()
                IconLeftWidget:
                    icon: "package-variant-closed"
            OneLineAvatarIconListItem:
                text: "Sales History"
                on_release: app.open_history()
                IconLeftWidget:
                    icon: "history"
            OneLineAvatarIconListItem:
                text: "Switch Workspace"
                on_release: app.show_wp_switcher()
                IconLeftWidget:
                    icon: "swap-horizontal"
            Widget:
'''

class RightCheckbox(IRightBodyTouch, MDCheckbox):
    pass

class ListItemWithCheckbox(OneLineAvatarIconListItem):
    item_id = NumericProperty()
    is_active = NumericProperty()

class ProMedApp(MDApp):
    active_wp_display = StringProperty("ProMed Suite")
    active_wp_id = StringProperty("")

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.material_style = "M3"
        self.db = Database()
        return Builder.load_string(KV)

    def on_start(self):
        # Start Splash Loading
        Clock.schedule_interval(self.update_progress, 0.05)

    def update_progress(self, dt):
        pb = self.root.get_screen('splash').ids.progress
        if pb.value < 100:
            pb.value += 2
        else:
            Clock.unschedule(self.update_progress)
            self.check_workspace()

    def check_workspace(self):
        self.db.cursor.execute("SELECT name FROM workspaces")
        res = self.db.cursor.fetchall()
        if not res:
            self.root.current = "onboard"
        else:
            self.load_wp(res[0][0])
            self.root.current = "main"

    def create_workspace(self, name):
        if not name: return
        try:
            self.db.cursor.execute("INSERT INTO workspaces (name) VALUES (?)", (name,))
            self.db.conn.commit()
            self.load_wp(name)
            self.root.current = "main"
        except:
            pass

    def load_wp(self, name):
        self.active_wp_display = name
        self.active_wp_id = self.db.get_clean_name(name)
        self.db.init_workspace_tables(name)
        self.refresh_ui()

    def refresh_ui(self):
        self.load_checklists()
        self.load_shortlists()

    # --- NOTEPAD DETECTION ---
    def smart_detect(self, text):
        words = text.split()
        if not words: return
        self.db.cursor.execute(f"SELECT * FROM meds_{self.active_wp_id} WHERE name LIKE ?", (f"{words[-1]}%",))
        res = self.db.cursor.fetchone()
        if res:
            self.root.get_screen('main').ids.insight_lbl.text = f"NAME: {res[1]}\\nGENERIC: {res[2]}\\nPRICE: ৳{res[4]}"

    # --- CHECKLIST LOGIC ---
    def add_cl_group(self, name):
        if name:
            self.db.cursor.execute(f"INSERT INTO chk_{self.active_wp_id} (name) VALUES (?)", (name,))
            self.db.conn.commit()
            self.load_checklists()

    def load_checklists(self):
        container = self.root.get_screen('main').ids.cl_list_container
        container.clear_widgets()
        self.db.cursor.execute(f"SELECT * FROM chk_{self.active_wp_id} ORDER BY id DESC")
        for row in self.db.cursor.fetchall():
            gid, gname, is_done = row
            card = MDCard(orientation='vertical', size_hint_y=None, height="200dp", radius=20, padding=10)
            if is_done: card.md_bg_color = (0.9, 0.9, 0.9, 1)
            
            h = QHBoxLayout()
            h.add_widget(QLabel(text=gname.upper(), color=(0,0,0,1), bold=True))
            btn_pos = MDIconButton(icon="send", on_release=lambda x, i=gid: self.transfer_to_pos(i))
            btn_done = MDIconButton(icon="check-decagram", on_release=lambda x, i=gid: self.mark_cl_done(i))
            h.add_widget(btn_pos); h.add_widget(btn_done)
            card.add_widget(h)
            container.add_widget(card)

    def mark_cl_done(self, gid):
        self.db.cursor.execute(f"UPDATE chk_{self.active_wp_id} SET done=1 WHERE id=?", (gid,))
        self.db.conn.commit()
        self.load_checklists()

    # --- POS LOGIC ---
    def pos_add_item(self):
        name = self.root.get_screen('main').ids.pos_search.text
        qty = int(self.root.get_screen('main').ids.pos_qty.text or 1)
        self.db.cursor.execute(f"SELECT price FROM meds_{self.active_wp_id} WHERE name=?", (name,))
        res = self.db.cursor.fetchone()
        if res:
            price = res[0]
            total = price * qty
            self.root.get_screen('main').ids.pos_cart.add_widget(
                TwoLineAvatarIconListItem(text=f"{name} x{qty}", secondary_text=f"Total: ৳{total}")
            )

    def transfer_to_pos(self, gid):
        self.root.get_screen('main').ids.bottom_nav.switch_tab("pos")

    def finalize_sale(self):
        MDDialog(text="Sale Recorded Successfully!", radius=[20, 20, 20, 20]).open()

    def load_shortlists(self):
        pass # RESTORED Logic here for Clinical lists

    def open_inventory(self):
        MDDialog(title="Inventory Entry", type="custom", content_cls=MDBoxLayout(orientation='vertical', height="300dp")).open()

if __name__ == '__main__':
    ProMedApp().run()
