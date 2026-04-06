import sys
import sqlite3
import re
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QLineEdit, QLabel, QPushButton, QStackedWidget, 
    QFrame, QCompleter, QScrollArea, QComboBox, QDialog, QFormLayout, 
    QMessageBox, QInputDialog, QFileDialog, QCheckBox, QProgressBar
)
from PyQt6.QtGui import QIcon, QPainter, QPixmap, QColor, QFont
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import Qt, QStringListModel, QByteArray, QSize, QPropertyAnimation, QRect, QEasingCurve, QTimer

# --- SVG REPOSITORY ---
SVG = {
    "logo": '''<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>''',
    "menu": '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>''',
    "note": '''<svg viewBox="0 0 24 24" fill="none" stroke="#0078D4" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8"/></svg>''',
    "check": '''<svg viewBox="0 0 24 24" fill="none" stroke="#0078D4" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>''',
    "short": '''<svg viewBox="0 0 24 24" fill="none" stroke="#0078D4" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h7"/></svg>''',
    "cart": '''<svg viewBox="0 0 24 24" fill="none" stroke="#0078D4" stroke-width="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>''',
    "trash": '''<svg viewBox="0 0 24 24" fill="none" stroke="#C42B1C" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>''',
    "plus": '''<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3"><path d="M12 5v14M5 12h14"/></svg>''',
    "tick": '''<svg viewBox="0 0 24 24" fill="none" stroke="#107C10" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>''',
    "send": '''<svg viewBox="0 0 24 24" fill="none" stroke="#0078D4" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>'''
}

def get_icon(name, size=24):
    renderer = QSvgRenderer(QByteArray(SVG[name].encode('utf-8')))
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter); painter.end()
    return QIcon(pixmap)

def clean_wp(name): return re.sub(r'\W+', '', name)

def safe_math(val):
    try: return float(str(val).replace('৳', '').replace(',', '').strip())
    except: return 0.0

# --- THEME STYLESHEET ---
STYLESHEET = """
    QMainWindow { background-color: #F8F9FA; }
    #Header { background-color: #0078D4; border-bottom-left-radius: 20px; border-bottom-right-radius: 20px; min-height: 70px; }
    #HeaderTitle { color: white; font-size: 18px; font-weight: 800; }
    QComboBox { background: rgba(255,255,255,0.2); border: none; color: white; padding: 5px 12px; border-radius: 12px; font-weight: bold; min-width: 140px; }
    #Drawer { background-color: #FFFFFF; border-right: 1px solid #EAEAEA; border-top-right-radius: 25px; border-bottom-right-radius: 25px; }
    #DrawerBtn { border: none; background: none; text-align: left; padding: 15px 25px; font-size: 14px; border-radius: 12px; margin: 3px 12px; color: #444; font-weight: 600; }
    #DrawerBtn:hover { background-color: #F0F7FF; color: #0078D4; }
    #CompactCard { background-color: #FFFFFF; border-radius: 15px; padding: 10px; margin: 4px 12px; border: 1px solid #EAEAEA; }
    #CardOrdered { background-color: #E9ECEF; border-radius: 15px; padding: 10px; margin: 4px 12px; opacity: 0.7; border: 1px solid #CCC; }
    QProgressBar { border: none; background: rgba(255,255,255,0.2); border-radius: 10px; height: 10px; }
    QProgressBar::chunk { background-color: white; border-radius: 10px; }
    QLineEdit, QTextEdit, QComboBox#Normal { border: 1px solid #D1D1D1; border-radius: 12px; padding: 10px; background: white; }
    QPushButton#Primary { background-color: #0078D4; color: white; border: none; padding: 12px; border-radius: 15px; font-weight: 700; }
    QPushButton#IconBtn { background: transparent; border: none; padding: 6px; border-radius: 10px; }
    QScrollArea { border: none; background: transparent; }
"""

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("med_pro_vFinal.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS workspaces (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)')
        self.conn.commit()

    def init_wp(self, wp):
        s = clean_wp(wp)
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS med_{s} (id INTEGER PRIMARY KEY, name TEXT UNIQUE, gen TEXT, co TEXT, cat TEXT, price REAL, img TEXT)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_{s} (id INTEGER PRIMARY KEY, name TEXT, done INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS chk_it_{s} (id INTEGER PRIMARY KEY, gid INTEGER, name TEXT, qty INTEGER, checked INTEGER DEFAULT 0)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS short_{s} (id INTEGER PRIMARY KEY, name TEXT)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS short_it_{s} (gid INTEGER, name TEXT, pwr TEXT, type TEXT)')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS sales_{s} (items TEXT, total REAL, date TEXT)')
        self.conn.commit()

class ProMedApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database(); self.active_wp = ""; self.img_path = ""
        self.setFixedSize(420, 850); self.setStyleSheet(STYLESHEET)
        
        container = QWidget(); self.setCentralWidget(container)
        self.root = QVBoxLayout(container); self.root.setContentsMargins(0,0,0,0); self.root.setSpacing(0)
        
        self.setup_header()
        self.pages = QStackedWidget(); self.root.addWidget(self.pages)
        self.setup_drawer()

        self.init_splash(); self.init_onboarding(); self.init_notepad()
        self.init_checklists(); self.init_shortlists(); self.init_inventory()
        self.init_pos(); self.init_history()

        self.pages.setCurrentIndex(0); self.start_loading()

    def setup_header(self):
        self.header = QFrame(objectName="Header"); h_lay = QHBoxLayout(self.header)
        self.menu_btn = QPushButton(); self.menu_btn.setIcon(get_icon("menu")); self.menu_btn.setObjectName("IconBtn")
        self.menu_btn.clicked.connect(self.toggle_drawer)
        self.wp_picker = QComboBox(); self.wp_picker.currentIndexChanged.connect(self.on_wp_change)
        h_lay.addWidget(self.menu_btn); h_lay.addStretch(); h_lay.addWidget(self.wp_picker); h_lay.addStretch()
        h_lay.addWidget(QLabel("ProMed", styleSheet="color:white; font-weight:bold;"))
        self.root.addWidget(self.header); self.header.hide()

    def setup_drawer(self):
        self.drawer = QFrame(self); self.drawer.setObjectName("Drawer"); self.drawer.setGeometry(-320, 70, 300, 780)
        lay = QVBoxLayout(self.drawer); lay.setContentsMargins(10,20,10,20)
        menus = [("Notepad", 2), ("Checklists", 3), ("Short Lists", 4), ("Inventory", 5), ("POS Terminal", 6), ("Sales History", 7)]
        for name, idx in menus:
            btn = QPushButton(f"  {name}"); btn.setObjectName("DrawerBtn"); btn.clicked.connect(lambda ch, i=idx: self.navigate(i))
            lay.addWidget(btn)
        lay.addStretch(); self.drawer.raise_()

    def toggle_drawer(self):
        x = 0 if self.drawer.x() < 0 else -320
        self.anim = QPropertyAnimation(self.drawer, b"geometry")
        self.anim.setDuration(250); self.anim.setEndValue(QRect(x, 70, 300, 780)); self.anim.start()

    def navigate(self, idx):
        self.pages.setCurrentIndex(idx); self.toggle_drawer()

    def init_splash(self):
        p = QWidget(); p.setStyleSheet("background:#0078D4;"); lay = QVBoxLayout(p); lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo = QLabel(); logo.setPixmap(get_icon("logo", 80).pixmap(80,80)); lay.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(QLabel("PROMED SUITE", styleSheet="color:white; font-size:22px; font-weight:900;"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.bar = QProgressBar(); self.bar.setFixedWidth(200); lay.addWidget(self.bar, alignment=Qt.AlignmentFlag.AlignCenter)
        self.pages.addWidget(p)

    def start_loading(self):
        self.load_v = 0; self.timer = QTimer(); self.timer.timeout.connect(self.update_splash); self.timer.start(20)

    def update_splash(self):
        self.load_v += 2; self.bar.setValue(self.load_v)
        if self.load_v >= 100:
            self.timer.stop(); self.check_db()

    def check_db(self):
        self.db.cursor.execute("SELECT name FROM workspaces")
        res = self.db.cursor.fetchall()
        if not res: self.pages.setCurrentIndex(1)
        else:
            self.header.show(); self.refresh_wp_dropdown(); self.switch_wp(res[0][0]); self.pages.setCurrentIndex(2)

    def refresh_wp_dropdown(self):
        self.wp_picker.blockSignals(True); self.wp_picker.clear()
        self.db.cursor.execute("SELECT name FROM workspaces")
        self.wp_picker.addItems([r[0] for r in self.db.cursor.fetchall()])
        self.wp_picker.addItem("+ New Place"); self.wp_picker.blockSignals(False)

    def on_wp_change(self):
        t = self.wp_picker.currentText()
        if t == "+ Add New Place":
            n, ok = QInputDialog.getText(self, "Setup", "Hospital Name:")
            if ok and n: self.db.cursor.execute("INSERT INTO workspaces (name) VALUES (?)", (n,)); self.db.conn.commit(); self.refresh_wp_dropdown(); self.wp_picker.setCurrentText(n)
        else: self.switch_wp(t)

    def switch_wp(self, name):
        self.active_wp = clean_wp(name); self.db.init_wp(name)
        self.update_completer(); self.refresh_inv(); self.refresh_cl(); self.refresh_sl(); self.refresh_hist()

    # --- PAGES ---
    def init_onboarding(self):
        p = QWidget(); p.setStyleSheet("background:#0078D4;"); lay = QVBoxLayout(p); lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(QLabel("Setup Workspace", styleSheet="color:white; font-size:24px; font-weight:bold;"))
        self.ob_in = QLineEdit(); self.ob_in.setPlaceholderText("Hospital Name..."); lay.addWidget(self.ob_in)
        btn = QPushButton("FINISH SETUP"); btn.setObjectName("Primary"); btn.setStyleSheet("background:white; color:#0078D4;"); btn.clicked.connect(self.save_ob)
        lay.addWidget(btn); self.pages.addWidget(p)

    def save_ob(self):
        n = self.ob_in.text().strip()
        if n: self.db.cursor.execute("INSERT INTO workspaces (name) VALUES (?)", (n,)); self.db.conn.commit(); self.check_db()

    def init_notepad(self):
        p = QWidget(); lay = QVBoxLayout(p); lay.setContentsMargins(15,15,15,15)
        self.note = QTextEdit(); self.note.setPlaceholderText("Notes..."); self.note.textChanged.connect(self.lookup)
        self.det = QFrame(objectName="CompactCard"); self.det.setFixedHeight(100); dv = QVBoxLayout(self.det)
        self.db_l = QLabel("Auto-detecting..."); dv.addWidget(QLabel("SMART INSIGHT", styleSheet="color:#0078D4; font-weight:bold;")); dv.addWidget(self.db_l)
        lay.addWidget(self.note); lay.addWidget(self.det); self.pages.addWidget(p)

    def lookup(self):
        txt = self.note.toPlainText().split()
        if txt:
            self.db.cursor.execute(f"SELECT * FROM med_{self.active_wp} WHERE name LIKE ?", (f"{txt[-1]}%",))
            r = self.db.cursor.fetchone()
            if r: self.db_l.setText(f"<b>{r[1].upper()}</b><br>৳{r[5]}")

    def init_checklists(self):
        p = QWidget(); lay = QVBoxLayout(p); h = QHBoxLayout(); h.setContentsMargins(15,5,15,5); self.cl_in = QLineEdit(); self.cl_in.setPlaceholderText("Group...")
        btn = QPushButton("+"); btn.setObjectName("Primary"); btn.clicked.connect(self.add_cl); h.addWidget(self.cl_in); h.addWidget(btn); lay.addLayout(h)
        self.cl_lay = QVBoxLayout(); w = QWidget(); w.setLayout(self.cl_lay); sc = QScrollArea(); sc.setWidget(w); sc.setWidgetResizable(True); lay.addWidget(sc); self.pages.addWidget(p)

    def add_cl(self):
        if self.cl_in.text(): self.db.cursor.execute(f"INSERT INTO chk_{self.active_wp} (name) VALUES (?)", (self.cl_in.text(),)); self.db.conn.commit(); self.cl_in.clear(); self.refresh_cl()

    def refresh_cl(self):
        while self.cl_lay.count() > 0:
            it = self.cl_lay.takeAt(0).widget()
            if it: it.deleteLater()
        self.db.cursor.execute(f"SELECT * FROM chk_{self.active_wp} ORDER BY id DESC")
        for rid, name, done in self.db.cursor.fetchall():
            card = QFrame(objectName="CardOrdered" if done else "CompactCard"); cv = QVBoxLayout(card)
            head = QHBoxLayout(); head.addWidget(QLabel(name.upper(), styleSheet="font-weight:bold;"))
            bt_tr, bt_ok, bt_dl = QPushButton(), QPushButton(), QPushButton()
            bt_tr.setIcon(get_icon("send", 18)); bt_ok.setIcon(get_icon("tick", 18)); bt_dl.setIcon(get_icon("trash", 18))
            bt_tr.clicked.connect(lambda ch, x=rid: self.transfer_pos(x))
            bt_ok.clicked.connect(lambda ch, x=rid: self.db.cursor.execute(f"UPDATE chk_{self.active_wp} SET done=1 WHERE id=?", (x,)) or self.db.conn.commit() or self.refresh_cl())
            bt_dl.clicked.connect(lambda ch, x=rid: self.db.cursor.execute(f"DELETE FROM chk_{self.active_wp} WHERE id=?", (x,)) or self.db.conn.commit() or self.refresh_cl())
            head.addStretch(); head.addWidget(bt_tr); head.addWidget(bt_ok); head.addWidget(bt_dl); cv.addLayout(head)
            self.db.cursor.execute(f"SELECT * FROM chk_it_{self.active_wp} WHERE gid=?", (rid,))
            for item in self.db.cursor.fetchall():
                rh = QHBoxLayout(); cb = QCheckBox(); cb.setChecked(bool(item[4]))
                cb.stateChanged.connect(lambda s, x=item[0]: self.db.cursor.execute(f"UPDATE chk_it_{self.active_wp} SET checked=? WHERE id=?", (1 if s==2 else 0, x)) or self.db.conn.commit())
                rh.addWidget(cb); rh.addWidget(QLabel(f"{item[2]} x{item[3]}")); cv.addLayout(rh)
            if not done:
                ih = QHBoxLayout(); ni, qi = QLineEdit(), QLineEdit(); qi.setFixedWidth(40)
                bi = QPushButton("+"); bi.clicked.connect(lambda ch, r=rid, n=ni, q=qi: self.db.cursor.execute(f"INSERT INTO chk_it_{self.active_wp} (gid, name, qty) VALUES (?,?,?)", (r, n.text(), int(q.text() or 1))) or self.db.conn.commit() or self.refresh_cl())
                ih.addWidget(ni); ih.addWidget(qi); ih.addWidget(bi); cv.addLayout(ih)
            self.cl_lay.addWidget(card)
        self.cl_lay.addStretch()

    def init_pos(self):
        p = QWidget(); lay = QVBoxLayout(p); lay.setContentsMargins(15,15,15,15)
        h = QHBoxLayout(); self.p_s, self.p_q = QLineEdit(), QLineEdit(); self.p_q.setFixedWidth(40); self.comp = QCompleter()
        self.p_s.setCompleter(self.comp); btn = QPushButton("Add"); btn.clicked.connect(self.pos_add)
        h.addWidget(self.p_s); h.addWidget(self.p_q); h.addWidget(btn); lay.addLayout(h)
        self.cart_lay = QVBoxLayout(); w = QWidget(); w.setLayout(self.cart_lay); sc = QScrollArea(); sc.setWidget(w); sc.setWidgetResizable(True); lay.addWidget(sc)
        btn_f = QPushButton("FINALIZE COLLECTION"); btn_f.setObjectName("Primary"); btn_f.clicked.connect(self.pos_fin); lay.addWidget(btn_f); self.pages.addWidget(p)

    def pos_add(self):
        n, q = self.p_s.text(), int(self.p_q.text() or 1)
        self.db.cursor.execute(f"SELECT price FROM med_{self.active_wp} WHERE name=?", (n,))
        r = self.db.cursor.fetchone()
        if r: self.add_pos_ui(n, q, r[0]); self.p_s.clear()

    def add_pos_ui(self, n, q, p):
        card = QFrame(objectName="CompactCard"); h = QHBoxLayout(card); h.addWidget(QLabel(f"<b>{n}</b> x{q}")); h.addStretch()
        h.addWidget(QLabel(str(p*q), objectName="Total")); bd = QPushButton(); bd.setIcon(get_icon("trash", 18)); bd.clicked.connect(lambda: card.deleteLater()); h.addWidget(bd); self.cart_lay.addWidget(card)

    def transfer_pos(self, gid):
        self.db.cursor.execute(f"SELECT name, qty FROM chk_it_{self.active_wp} WHERE gid=?", (gid,))
        for n, q in self.db.cursor.fetchall():
            self.db.cursor.execute(f"SELECT price FROM med_{self.active_wp} WHERE name=?", (n,))
            r = self.db.cursor.fetchone(); pr = r[0] if r else 0.0
            if pr == 0.0:
                pr, ok = QInputDialog.getDouble(self, "Price", f"Price for {n}:", 0, 0, 99999, 1)
                if not ok: continue
            self.add_pos_ui(n, q, pr)
        self.pages.setCurrentIndex(6)

    def pos_fin(self):
        itms, grand = [], 0.0
        for i in range(self.cart_lay.count()):
            w = self.cart_lay.itemAt(i).widget()
            if w:
                lbls = w.findChildren(QLabel); itms.append(lbls[0].text()); grand += safe_math(lbls[1].text())
        if itms:
            self.db.cursor.execute(f"INSERT INTO sales_{self.active_wp} (items, total, date) VALUES (?,?,?)", (", ".join(itms), grand, datetime.now().strftime("%d/%m %H:%M"))); self.db.conn.commit()
            while self.cart_lay.count() > 0:
                it = self.cart_lay.takeAt(0).widget()
                if it: it.deleteLater()
            self.refresh_hist()

    def update_completer(self):
        self.db.cursor.execute(f"SELECT name FROM med_{self.active_wp}"); self.comp.setModel(QStringListModel([r[0] for r in self.db.cursor.fetchall()]))

    def init_shortlists(self):
        p = QWidget(); lay = QVBoxLayout(p); h = QHBoxLayout(); self.sl_in = QLineEdit(); btn = QPushButton("+")
        btn.clicked.connect(self.add_sl); h.addWidget(self.sl_in); h.addWidget(btn); lay.addLayout(h)
        self.sl_cont = QVBoxLayout(); w = QWidget(); w.setLayout(self.sl_cont); sc = QScrollArea(); sc.setWidget(w); sc.setWidgetResizable(True); lay.addWidget(sc); self.pages.addWidget(p)

    def add_sl(self):
        if self.sl_in.text(): self.db.cursor.execute(f"INSERT INTO short_{self.active_wp} (name) VALUES (?)", (self.sl_in.text(),)); self.db.conn.commit(); self.refresh_sl()

    def refresh_sl(self):
        while self.sl_cont.count() > 0:
            it = self.sl_cont.takeAt(0).widget()
            if it: it.deleteLater()
        self.db.cursor.execute(f"SELECT * FROM short_{self.active_wp} ORDER BY id DESC")
        for r in self.db.cursor.fetchall():
            card = QFrame(objectName="CompactCard"); cv = QVBoxLayout(card); cv.addWidget(QLabel(r[1].upper(), styleSheet="font-weight:bold;"))
            ih = QHBoxLayout(); ni = QLineEdit(); bi = QPushButton("+")
            bi.clicked.connect(lambda ch, rx=r[0], nix=ni: self.db.cursor.execute(f"INSERT INTO short_it_{self.active_wp} (gid, name) VALUES (?,?)", (rx, nix.text())) or self.db.conn.commit() or self.refresh_sl())
            ih.addWidget(ni); ih.addWidget(bi); cv.addLayout(ih)
            self.db.cursor.execute(f"SELECT name FROM short_it_{self.active_wp} WHERE gid=?", (r[0],))
            for item in self.db.cursor.fetchall(): cv.addWidget(QLabel(f"• {item[0]}"))
            self.sl_cont.addWidget(card)
        self.sl_cont.addStretch()

    def init_inventory(self):
        p = QWidget(); lay = QVBoxLayout(p); btn = QPushButton("NEW PRODUCT"); btn.clicked.connect(self.inv_pop); lay.addWidget(btn)
        self.i_cont = QVBoxLayout(); w = QWidget(); w.setLayout(self.i_cont); sc = QScrollArea(); sc.setWidget(w); sc.setWidgetResizable(True); lay.addWidget(sc); self.pages.addWidget(p)

    def inv_pop(self):
        d = QDialog(self); l = QFormLayout(d); n, pr = QLineEdit(), QLineEdit()
        b = QPushButton("Save"); b.clicked.connect(d.accept); l.addRow("Name", n); l.addRow("Price", pr); l.addRow(b)
        if d.exec(): 
            try: self.db.cursor.execute(f"INSERT INTO med_{self.active_wp} (name, price) VALUES (?,?)", (n.text(), float(pr.text() or 0))); self.db.conn.commit(); self.refresh_inv(); self.update_completer()
            except: pass

    def refresh_inv(self):
        while self.i_cont.count() > 0:
            it = self.i_cont.takeAt(0).widget()
            if it: it.deleteLater()
        self.db.cursor.execute(f"SELECT * FROM med_{self.active_wp}")
        for r in self.db.cursor.fetchall():
            self.i_cont.addWidget(QLabel(f"<b>{r[1]}</b><br>৳{r[5]}", objectName="CompactCard"))

    def init_history(self):
        p = QWidget(); lay = QVBoxLayout(p); self.h_cont = QVBoxLayout(); w = QWidget(); w.setLayout(self.h_cont); sc = QScrollArea(); sc.setWidget(w); sc.setWidgetResizable(True); lay.addWidget(sc); self.pages.addWidget(p)

    def refresh_hist(self):
        while self.h_cont.count() > 0:
            it = self.h_cont.takeAt(0).widget()
            if it: it.deleteLater()
        self.db.cursor.execute(f"SELECT * FROM sales_{self.active_wp} ORDER BY rowid DESC")
        for r in self.db.cursor.fetchall():
            card = QFrame(objectName="CompactCard"); v = QVBoxLayout(card); v.addWidget(QLabel(f"<b>৳{r[1]}</b> — {r[2]}")); v.addWidget(QLabel(r[0][:100])); self.h_cont.addWidget(card)

if __name__ == "__main__":
    app = QApplication(sys.argv); win = ProMedApp(); win.show(); sys.exit(app.exec())
