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

# --- DATABASE ENGINE (v1.0.3 Workspace Isolation) ---
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
        # 1. Inventory Table (Full Profile)
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS meds_{s} (id INTEGER PRIMARY KEY, name TEXT UNIQUE, gen TEXT, co TEXT, cat TEXT, price REAL, img TEXT)')
        # 2. Checklist Tables
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_{s} (id INTEGER PRIMARY KEY, name TEXT, is_done INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_it_{s} (id INTEGER PRIMARY KEY, gid INTEGER, name TEXT, qty INTEGER, is_checked INTEGER DEFAULT 0)')
        # 3. Clinical Shortlist Tables
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS short_{s} (id INTEGER PRIMARY KEY, name TEXT)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS short_it_{s} (id INTEGER PRIMARY KEY, gid INTEGER, name TEXT, pwr TEXT, type TEXT)')
        # 4. Sales History
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS sales_{s} (id INTEGER PRIMARY KEY, items TEXT, total REAL, date TEXT)')
        self.conn.commit()

# --- UI DESIGN (Aero Smooth Theme) ---
KV = '''
<CheckItemListItem>:
    IconLeftWidget:
        icon: "pill"
    RightCheckbox:
        active: root.checked
        on_active: app.toggle_item_check(root.item_id, self.active)

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
            text: "PROMED v1.0.3"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            font_style: "H5"
            bold: True
        MDProgressBar:
            id: progress
            value: 0
            size_hint_x: .6
            pos_hint: {"center_x": .5, "center_y": .3}
            color: 1, 1, 1, 1

<OnboardScreen>:
    name: "onboard"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0, 0.47, 0.83, 1
        padding: "40dp"
        spacing: "20dp"
        MDLabel:
            text: "Medical Setup"
            font_style: "H4"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            bold: True
        MDTextField:
            id: wp_name
            hint_text: "Hospital or Clinic Name"
            mode: "round"
            fill_color_normal: 1, 1, 1, 1
        MDRaisedButton:
            text: "INITIALIZE WORKSPACE"
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
            right_action_items: [["swap-horizontal", lambda x: app.show_wp_dialog()]]

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
                        hint_text: "Clinical Notes..."
                        multiline: True
                        on_text: app.detect_med(self.text)
                    MDCard:
                        size_hint_y: None
                        height: "110dp"
                        radius: 25
                        padding: "15dp"
                        elevation: 1
                        MDLabel:
                            id: insight_lbl
                            text: "Smart Insight Active"
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
                            hint_text: "New Group"
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
                            id: pos_search
                            hint_text: "Search med..."
                        MDTextField:
                            id: pos_qty
                            hint_text: "Qty"
                            size_hint_x: .2
                            text: "1"
                        MDIconButton:
                            icon: "plus-box"
                            on_release: app.pos_add_item()
                    ScrollView:
                        MDList:
                            id: pos_cart
                    MDRaisedButton:
                        text: "FINALIZE & COLLECT"
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
                text: "Suite Explorer"
                font_style: "Button"
            OneLineAvatarIconListItem:
                text: "Inventory"
                on_release: app.nav_to("inventory")
                IconLeftWidget:
                    icon: "package-variant-closed"
            OneLineAvatarIconListItem:
                text: "Shortlists"
                on_release: app.nav_to("shortlist")
                IconLeftWidget:
                    icon: "layers"
            OneLineAvatarIconListItem:
                text: "Sales History"
                on_release: app.nav_to("history")
                IconLeftWidget:
                    icon: "history"
            Widget:

# --- SUB SCREENS ---
<InventoryScreen>:
    name: "inventory"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Inventory"
            left_action_items: [["arrow-left", lambda x: app.back_home()]]
        MDRaisedButton:
            text: "ADD PRODUCT"
            size_hint_x: 1
            on_release: app.open_inv_dialog()
        ScrollView:
            MDList:
                id: inv_list

<ShortlistScreen>:
    name: "shortlist"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Clinical Shortlists"
            left_action_items: [["arrow-left", lambda x: app.back_home()]]
        MDBoxLayout:
            size_hint_y: None
            height: "60dp"
            padding: "10dp"
            MDTextField:
                id: sl_name
                hint_text: "Group Name"
            MDIconButton:
                icon: "plus"
                on_release: app.add_sl_group(sl_name.text)
        ScrollView:
            MDList:
                id: sl_list

<HistoryScreen>:
    name: "history"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "History Logs"
            left_action_items: [["arrow-left", lambda x: app.back_home()]]
        ScrollView:
            MDList:
                id: hist_list
'''

class RightCheckbox(IRightBodyTouch, MDCheckbox): pass
class CheckItemListItem(OneLineAvatarIconListItem):
    item_id = NumericProperty()
    checked = BooleanProperty(False)

class InventoryScreen(Screen): pass
class ShortlistScreen(Screen): pass
class HistoryScreen(Screen): pass

class ProMedApp(MDApp):
    active_wp_display = StringProperty("ProMed")
    wp_slug = ""

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.material_style = "M3"
        self.sm = ScreenManager(transition=SlideTransition())
        self.sm.add_widget(Builder.load_string(KV))
        self.sm.add_widget(InventoryScreen())
        self.sm.add_widget(ShortlistScreen())
        self.sm.add_widget(HistoryScreen())
        return self.sm

    def on_start(self):
        db_path = os.path.join(self.user_data_dir, "promed_beta_v103.db")
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
            self.db.conn.commit()
            self.load_workspace(name)

    def load_workspace(self, name):
        self.active_wp_display = name
        self.wp_slug = self.db.get_slug(name)
        self.db.init_wp_tables(name)
        self.sm.current = "main"
        self.refresh_all()

    def refresh_all(self):
        self.refresh_cl()
        self.refresh_inv()
        self.refresh_hist()

    # --- INVENTORY LOGIC ---
    def open_inv_dialog(self):
        self.dialog = MDDialog(
            title="Register Product", type="custom",
            content_cls=MDBoxLayout(orientation="vertical", spacing="12dp", adaptive_height=True),
            buttons=[MDRaisedButton(text="SAVE", on_release=self.save_inv)]
        )
        self.dialog.content_cls.add_widget(MDTextField(hint_text="Med Name", id="n"))
        self.dialog.content_cls.add_widget(MDTextField(hint_text="Generic", id="g"))
        self.dialog.content_cls.add_widget(MDTextField(hint_text="Price", id="p"))
        self.dialog.open()

    def save_inv(self, *args):
        inputs = self.dialog.content_cls.children
        name, gen, price = inputs[2].text, inputs[1].text, inputs[0].text
        if name and price:
            self.db.cursor.execute(f"INSERT INTO meds_{self.wp_slug} (name, generic, price) VALUES (?,?,?)", (name, gen, float(price)))
            self.db.conn.commit(); self.refresh_inv(); self.dialog.dismiss()

    def refresh_inv(self):
        lst = self.sm.get_screen('inventory').ids.inv_list; lst.clear_widgets()
        self.db.cursor.execute(f"SELECT * FROM meds_{self.wp_slug}")
        for r in self.db.cursor.fetchall():
            lst.add_widget(TwoLineAvatarIconListItem(text=r[1], secondary_text=f"৳{r[4]}"))

    # --- CHECKLIST LOGIC ---
    def add_cl_group(self, name):
        if name:
            self.db.cursor.execute(f"INSERT INTO chk_{self.wp_slug} (name) VALUES (?)", (name,))
            self.db.conn.commit(); self.refresh_cl()

    def refresh_cl(self):
        cont = self.sm.get_screen('main').ids.cl_container; cont.clear_widgets()
        self.db.cursor.execute(f"SELECT * FROM chk_{self.wp_slug} ORDER BY id DESC")
        for gid, name, done in self.db.cursor.fetchall():
            card = MDCard(orientation='vertical', size_hint_y=None, height="140dp", radius=25, padding=15)
            if done: card.md_bg_color = (0.85, 0.85, 0.85, 1)
            h = BoxLayout(orientation='horizontal')
            h.add_widget(MDLabel(text=name.upper(), bold=True))
            h.add_widget(MDIconButton(icon="send", on_release=lambda x, i=gid: self.transfer_pos(i)))
            h.add_widget(MDIconButton(icon="check-decagram", on_release=lambda x, i=gid: self.mark_done(i)))
            card.add_widget(h)
            
            self.db.cursor.execute(f"SELECT name, qty FROM chk_it_{self.wp_slug} WHERE gid=?", (gid,))
            for n, q in self.db.cursor.fetchall():
                card.add_widget(MDLabel(text=f"• {n} x{q}", font_style="Caption"))
            cont.add_widget(card)

    def mark_done(self, gid):
        self.db.cursor.execute(f"UPDATE chk_{self.wp_slug} SET is_done=1 WHERE id=?", (gid,))
        self.db.conn.commit(); self.refresh_cl()

    # --- POS MATH ---
    def pos_add_item(self):
        name = self.sm.get_screen('main').ids.pos_search.text
        qty = int(self.sm.get_screen('main').ids.pos_qty.text or 1)
        self.db.cursor.execute(f"SELECT price FROM meds_{self.wp_slug} WHERE name=?", (name,))
        res = self.db.cursor.fetchone()
        if res:
            price = res[0]
            self.sm.get_screen('main').ids.pos_cart.add_widget(
                TwoLineAvatarIconListItem(text=f"{name} x{qty}", secondary_text=f"Total: ৳{price * qty}")
            )
        else: MDDialog(text="Medicine not in Inventory!").open()

    def finalize_sale(self):
        MDDialog(title="Payment", text="Sale Recorded!").open()

    def detect_med(self, text):
        w = text.split()
        if w:
            self.db.cursor.execute(f"SELECT * FROM meds_{self.wp_slug} WHERE name LIKE ?", (f"{w[-1]}%",))
            r = self.db.cursor.fetchone()
            if r: self.sm.get_screen('main').ids.insight_lbl.text = f"{r[1]} | ৳{r[4]}"

    def nav_to(self, scr): self.sm.current = scr; self.sm.get_screen('main').ids.nav_drawer.set_state("close")
    def back_home(self): self.sm.current = "main"
    def refresh_hist(self): pass
    def add_sl_group(self, name): pass
    def refresh_shortlists(self): pass
    def show_wp_dialog(self): pass

if __name__ == '__main__':
    ProMedApp().run()
