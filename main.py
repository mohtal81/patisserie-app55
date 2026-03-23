"""
Patisserie Orientale - Kivy + SQLite
Version amelioree : police agrandie, filtres par date, bugs fixes, UI amélioree
+ Mode Dark/Light, Benefice au dashboard, Statuts simplifies (en_cours / terminee)
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window

import database as db
import os
from datetime import datetime

# ── Theme manager ─────────────────────────────────────
class Theme:
    _dark = True  # default dark

    # Palettes dark
    DARK = dict(
        BG     = (0.07, 0.06, 0.10, 1),
        CARD   = (0.13, 0.11, 0.18, 1),
        CARD2  = (0.17, 0.14, 0.24, 1),
        TEXT   = (0.95, 0.92, 0.85, 1),
        MUTED  = (0.55, 0.52, 0.48, 1),
        INPUT  = (0.18, 0.16, 0.24, 1),
        NAV    = (0.11, 0.09, 0.16, 1),
    )
    # Palettes light
    LIGHT = dict(
        BG     = (0.96, 0.94, 0.90, 1),
        CARD   = (1.00, 0.98, 0.95, 1),
        CARD2  = (0.92, 0.89, 0.84, 1),
        TEXT   = (0.10, 0.08, 0.12, 1),
        MUTED  = (0.45, 0.42, 0.38, 1),
        INPUT  = (0.88, 0.86, 0.82, 1),
        NAV    = (0.90, 0.88, 0.84, 1),
    )

    # Couleurs communes (inchangees selon theme)
    ACCENT  = (0.85, 0.60, 0.15, 1)
    ACCENT2 = (0.55, 0.25, 0.70, 1)
    GREEN   = (0.20, 0.75, 0.45, 1)
    RED     = (0.85, 0.25, 0.25, 1)
    ORANGE  = (0.90, 0.50, 0.10, 1)
    BLUE    = (0.20, 0.55, 0.90, 1)

    @classmethod
    def is_dark(cls):
        return cls._dark

    @classmethod
    def set_dark(cls, val):
        cls._dark = val
        p = cls.DARK if val else cls.LIGHT
        Window.clearcolor = p["BG"]

    @classmethod
    def get(cls, key):
        p = cls.DARK if cls._dark else cls.LIGHT
        return p.get(key, cls.__dict__.get(key, (1,1,1,1)))

# Raccourcis globaux (lus dynamiquement)
def C(key): return Theme.get(key)

# Couleurs statiques (ne changent pas avec le theme)
C_ACCENT  = Theme.ACCENT
C_ACCENT2 = Theme.ACCENT2
C_GREEN   = Theme.GREEN
C_RED     = Theme.RED
C_ORANGE  = Theme.ORANGE
C_BLUE    = Theme.BLUE

Window.clearcolor = Theme.get("BG")

# ── Tailles de police globales (agrandies) ───────────
FS_TITLE  = dp(18)
FS_HEAD   = dp(16)
FS_BODY   = dp(15)
FS_SMALL  = dp(13)
FS_MICRO  = dp(12)
FS_BTN    = dp(15)
FS_KPI    = dp(20)

# ── Statuts simplifies ───────────────────────────────
STATUT_LABELS = {
    "en_cours":  "En cours",
    "terminee":  "Terminee",
}
STATUT_COLORS = {
    "en_cours": C_ACCENT,
    "terminee": C_GREEN,
}


# ================================================================================
#  UI HELPERS
# ================================================================================

def make_label(text, size=None, color=None, bold=False, halign="left", **kw):
    if size is None:
        size = FS_BODY
    if color is None:
        color = Theme.get("TEXT")
    lbl = Label(
        text=text, font_size=size, color=color, bold=bold,
        halign=halign, valign="middle", text_size=(None, None), **kw
    )
    lbl.bind(size=lambda o, v: setattr(o, "text_size", (v[0], None)))
    return lbl


def make_button(text, color=None, text_color=None,
                height=dp(48), on_press=None, font_size=None, bold=True):
    if color is None:
        color = C_ACCENT
    if text_color is None:
        text_color = (0.07, 0.06, 0.10, 1)
    if font_size is None:
        font_size = FS_BTN
    btn = Button(
        text=text, font_size=font_size, bold=bold,
        color=text_color, background_normal="",
        background_color=(0, 0, 0, 0),
        size_hint_y=None, height=height,
    )
    with btn.canvas.before:
        col = Color(*color)
        rr = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(12)])
    btn.bind(pos=lambda o, v: setattr(rr, "pos", v))
    btn.bind(size=lambda o, v: setattr(rr, "size", v))
    if on_press:
        btn.bind(on_press=on_press)
    return btn


def make_input(hint, height=dp(48), multiline=False, input_filter=None):
    ti = TextInput(
        hint_text=hint, multiline=multiline,
        size_hint_y=None, height=height,
        background_normal="", background_active="",
        background_color=Theme.get("INPUT"),
        foreground_color=Theme.get("TEXT"),
        hint_text_color=(*Theme.get("MUTED")[:3], 0.7),
        cursor_color=C_ACCENT,
        font_size=FS_BODY,
        padding=[dp(12), dp(12)],
    )
    if input_filter:
        ti.input_filter = input_filter
    return ti


def make_spinner(values, text=None, height=dp(48)):
    sp = Spinner(
        text=text or (values[0] if values else ""),
        values=values,
        size_hint_y=None, height=height,
        background_normal="", background_color=Theme.get("INPUT"),
        color=Theme.get("TEXT"), font_size=FS_BODY,
    )
    return sp


def card_bg(widget, color=None, radius=dp(12)):
    if color is None:
        color = Theme.get("CARD")
    with widget.canvas.before:
        col = Color(*color)
        rr = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[radius])
    widget.bind(pos=lambda o, v: setattr(rr, "pos", v))
    widget.bind(size=lambda o, v: setattr(rr, "size", v))


def show_popup(title, message, color=None):
    if color is None:
        color = C_GREEN
    content = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(14))
    content.add_widget(make_label(message, size=FS_BODY, halign="center"))
    btn = make_button("OK", color=color)
    content.add_widget(btn)
    pop = Popup(
        title=title, content=content,
        size_hint=(0.88, 0.38),
        background_color=Theme.get("CARD"), title_color=Theme.get("TEXT"),
        title_size=FS_HEAD,
    )
    btn.bind(on_press=pop.dismiss)
    pop.open()


def confirm_popup(title, message, on_confirm):
    content = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(14))
    content.add_widget(make_label(message, size=FS_BODY, halign="center"))
    btns = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
    btn_ok = make_button("Confirmer", color=C_RED, text_color=Theme.get("TEXT"))
    btn_no = make_button("Annuler",   color=Theme.get("MUTED"), text_color=Theme.get("TEXT"))
    btns.add_widget(btn_ok)
    btns.add_widget(btn_no)
    content.add_widget(btns)
    pop = Popup(
        title=title, content=content,
        size_hint=(0.88, 0.42),
        background_color=Theme.get("CARD"), title_color=Theme.get("TEXT"),
        title_size=FS_HEAD,
    )
    def _ok(inst):
        pop.dismiss()
        on_confirm()
    btn_ok.bind(on_press=_ok)
    btn_no.bind(on_press=pop.dismiss)
    pop.open()


# ================================================================================
#  FILTRE DE DATES — widget reutilisable
# ================================================================================

PERIOD_LABELS = [
    ("all",     "Tout"),
    ("today",   "Aujourd'hui"),
    ("week",    "Semaine"),
    ("month",   "Mois"),
    ("month3",  "3 mois"),
    ("year",    "Annee"),
    ("custom",  "Dates..."),
]


class DateFilterBar(BoxLayout):
    def __init__(self, on_change, **kw):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(4),
            **kw
        )
        self.on_change = on_change
        self._period   = "all"
        self._debut    = None
        self._fin      = None

        row1 = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        self._period_btns = {}
        for key, label in PERIOD_LABELS[:6]:
            btn = Button(
                text=label,
                font_size=FS_MICRO,
                background_normal="",
                background_color=(0, 0, 0, 0),
                color=Theme.get("MUTED"),
                size_hint_x=1,
            )
            with btn.canvas.before:
                col = Color(*Theme.get("CARD"))
                rr = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(8)])
            btn.bind(pos=lambda o, v: setattr(rr, "pos", v))
            btn.bind(size=lambda o, v: setattr(rr, "size", v))
            btn._bg_col = col
            btn._bg_rr  = rr
            btn.bind(on_press=lambda inst, k=key: self._set(k))
            self._period_btns[key] = btn
            row1.add_widget(btn)

        btn_custom = Button(
            text="Dates...",
            font_size=FS_MICRO,
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=Theme.get("MUTED"),
            size_hint_x=None,
            width=dp(72),
        )
        with btn_custom.canvas.before:
            col2 = Color(*Theme.get("CARD"))
            rr2  = RoundedRectangle(pos=btn_custom.pos, size=btn_custom.size, radius=[dp(8)])
        btn_custom.bind(pos=lambda o, v: setattr(rr2, "pos", v))
        btn_custom.bind(size=lambda o, v: setattr(rr2, "size", v))
        btn_custom._bg_col = col2
        btn_custom._bg_rr  = rr2
        btn_custom.bind(on_press=lambda inst: self._popup_custom())
        self._period_btns["custom"] = btn_custom
        row1.add_widget(btn_custom)

        self.add_widget(row1)

        self._lbl_range = make_label("", size=FS_MICRO, color=C_ACCENT, halign="center")
        self._lbl_range.size_hint_y = None
        self._lbl_range.height = dp(20)
        self.add_widget(self._lbl_range)

        self.height = dp(64)
        self._highlight("all")

    def _highlight(self, key):
        for k, btn in self._period_btns.items():
            is_sel = (k == key)
            btn._bg_col.rgba = C_ACCENT2 if is_sel else Theme.get("CARD")
            btn.color = Theme.get("TEXT") if is_sel else Theme.get("MUTED")

    def _set(self, key):
        self._period = key
        debut, fin = db.get_date_range_for_period(key)
        self._debut = debut
        self._fin   = fin
        self._highlight(key)
        if debut and fin:
            self._lbl_range.text = f"{debut}  →  {fin}"
        else:
            self._lbl_range.text = "Toutes les dates"
        self.on_change(debut, fin)

    def _popup_custom(self):
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        content.add_widget(make_label("Date debut  (AAAA-MM-JJ)", size=FS_SMALL, color=Theme.get("MUTED")))
        f_debut = make_input("ex: 2025-01-01")
        content.add_widget(f_debut)
        content.add_widget(make_label("Date fin  (AAAA-MM-JJ)", size=FS_SMALL, color=Theme.get("MUTED")))
        f_fin = make_input("ex: 2025-12-31")
        content.add_widget(f_fin)

        row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        today = datetime.now().date()
        for lbl, d, f in [
            ("Ce mois", today.replace(day=1), today),
            ("Mois prec.", (today.replace(day=1) - __import__('datetime').timedelta(days=1)).replace(day=1),
                           today.replace(day=1) - __import__('datetime').timedelta(days=1)),
        ]:
            b = make_button(lbl, height=dp(36), font_size=FS_MICRO,
                            color=Theme.get("CARD2"), text_color=Theme.get("TEXT"))
            _d, _f = str(d), str(f)
            b.bind(on_press=lambda inst, dd=_d, ff=_f: (
                setattr(f_debut, "text", dd),
                setattr(f_fin, "text", ff)
            ))
            row.add_widget(b)
        content.add_widget(row)

        btn_ok = make_button("Appliquer", color=C_GREEN)
        content.add_widget(btn_ok)

        pop = Popup(title="Plage personnalisee", content=content,
                    size_hint=(0.90, 0.60),
                    background_color=Theme.get("BG"), title_color=C_ACCENT,
                    title_size=FS_HEAD)

        def _apply(inst):
            debut = f_debut.text.strip()
            fin   = f_fin.text.strip()
            if not debut or not fin:
                show_popup("Erreur", "Remplissez les deux dates.", C_RED)
                return
            try:
                datetime.strptime(debut, "%Y-%m-%d")
                datetime.strptime(fin,   "%Y-%m-%d")
            except ValueError:
                show_popup("Erreur", "Format invalide : AAAA-MM-JJ", C_RED)
                return
            self._debut = debut
            self._fin   = fin
            self._period = "custom"
            self._highlight("custom")
            self._lbl_range.text = f"{debut}  →  {fin}"
            pop.dismiss()
            self.on_change(debut, fin)

        btn_ok.bind(on_press=_apply)
        pop.open()


# ================================================================================
#  NAV BAR
# ================================================================================

class NavBar(BoxLayout):
    def __init__(self, manager, **kw):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None, height=dp(62),
            padding=[dp(4), dp(6)], spacing=dp(4), **kw
        )
        with self.canvas.before:
            self._nav_col = Color(*Theme.get("NAV"))
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda o, v: setattr(self._bg, "pos", v))
        self.bind(size=lambda o, v: setattr(self._bg, "size", v))

        self.manager = manager
        self._btns = {}
        tabs = [
            ("🏠", "dashboard"),
            ("📦", "stock"),
            ("🛒", "achats"),
            ("🎂", "produits"),
            ("📋", "commandes"),
            ("⚙",  "params"),
        ]
        for icon, screen in tabs:
            btn = Button(
                text=icon, font_size=dp(26),
                background_normal="", background_color=(0, 0, 0, 0),
                color=Theme.get("MUTED"),
            )
            btn.bind(on_press=lambda inst, s=screen: self.goto(s))
            self._btns[screen] = btn
            self.add_widget(btn)

    def goto(self, screen_name):
        for name, btn in self._btns.items():
            btn.color = C_ACCENT if name == screen_name else Theme.get("MUTED")
        self.manager.current = screen_name

    def highlight(self, screen_name):
        for name, btn in self._btns.items():
            btn.color = C_ACCENT if name == screen_name else Theme.get("MUTED")

    def apply_theme(self):
        self._nav_col.rgba = Theme.get("NAV")
        self.highlight(self.manager.current)


# ================================================================================
#  BASE SCREEN
# ================================================================================

class BaseScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.root_layout = BoxLayout(orientation="vertical", spacing=0)
        self.add_widget(self.root_layout)

    def set_navbar(self, navbar):
        self.navbar = navbar

    def on_pre_enter(self):
        if hasattr(self, "navbar"):
            self.navbar.highlight(self.name)
        self.refresh()

    def refresh(self):
        pass


# ================================================================================
#  DASHBOARD avec filtre de dates + benefice
# ================================================================================

class DashboardScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(name="dashboard", **kw)
        self._date_debut = None
        self._date_fin   = None
        self._build()

    def _build(self):
        root = self.root_layout

        header = BoxLayout(size_hint_y=None, height=dp(62), padding=[dp(16), 0])
        header.add_widget(make_label(
            "Patisserie Orientale", size=FS_TITLE, bold=True, color=C_ACCENT
        ))
        root.add_widget(header)

        self._filter_bar = DateFilterBar(
            on_change=self._on_date_change,
            padding=[dp(10), dp(4)],
        )
        root.add_widget(self._filter_bar)

        sep = Widget(size_hint_y=None, height=dp(1))
        with sep.canvas:
            Color(*Theme.get("CARD"))
            Rectangle(pos=sep.pos, size=sep.size)
        root.add_widget(sep)

        scroll = ScrollView()
        self.content = BoxLayout(
            orientation="vertical", spacing=dp(10),
            padding=[dp(12), dp(8), dp(12), dp(16)],
            size_hint_y=None
        )
        self.content.bind(minimum_height=self.content.setter("height"))
        scroll.add_widget(self.content)
        root.add_widget(scroll)

    def _on_date_change(self, debut, fin):
        self._date_debut = debut
        self._date_fin   = fin
        self.refresh()

    def refresh(self):
        self.content.clear_widgets()
        stats = db.get_stats(self._date_debut, self._date_fin)

        # Calcul benefice
        ca         = stats.get("ca_total", 0)
        depenses   = stats.get("depenses_achats", 0)
        benefice   = ca - depenses
        ben_color  = C_GREEN if benefice >= 0 else C_RED

        # KPI row 1
        kpis = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(100))
        kpis.add_widget(self._kpi("Commandes\nattente",  str(stats["commandes_attente"]), C_ORANGE))
        kpis.add_widget(self._kpi("CA\n(livrees)",       f"{ca:,.0f} DA",                 C_GREEN))
        kpis.add_widget(self._kpi("Alertes\nstock",      str(stats["nb_alertes"]),         C_RED))
        self.content.add_widget(kpis)

        # KPI row 2
        kpis2 = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(100))
        kpis2.add_widget(self._kpi("Valeur\nstock",  f"{stats['valeur_stock']:,.0f} DA",  C_ACCENT2))
        kpis2.add_widget(self._kpi("Total\ncmds",    str(stats["commandes_total"]),        C_ACCENT))
        kpis2.add_widget(self._kpi("Terminees",      str(stats.get("commandes_livrees", 0)), C_BLUE))
        self.content.add_widget(kpis2)

        # Bande Depenses + Benefice
        fin_row = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(8),
                            padding=[dp(0), dp(0)])

        dep_box = BoxLayout(size_hint_y=None, height=dp(52), padding=[dp(12), dp(8)],
                            spacing=dp(4))
        card_bg(dep_box, Theme.get("CARD"))
        dep_box.add_widget(make_label("Depenses :", size=FS_SMALL,
                                      color=Theme.get("MUTED")))
        dep_box.add_widget(make_label(
            f"{depenses:,.0f} DA",
            size=FS_SMALL, bold=True, color=C_ORANGE, halign="right"
        ))

        ben_box = BoxLayout(size_hint_y=None, height=dp(52), padding=[dp(12), dp(8)],
                            spacing=dp(4))
        card_bg(ben_box, Theme.get("CARD"))
        ben_box.add_widget(make_label("Benefice :", size=FS_SMALL,
                                      color=Theme.get("MUTED")))
        ben_box.add_widget(make_label(
            f"{benefice:,.0f} DA",
            size=FS_SMALL, bold=True, color=ben_color, halign="right"
        ))

        fin_row.add_widget(dep_box)
        fin_row.add_widget(ben_box)
        self.content.add_widget(fin_row)

        # Alertes stock
        alertes = db.get_stock_alerts()
        if alertes:
            self.content.add_widget(make_label(
                f"⚠  {len(alertes)} ingredient(s) en rupture / stock faible",
                color=C_RED, bold=True, size=FS_SMALL
            ))
            for a in alertes:
                box = BoxLayout(size_hint_y=None, height=dp(40), padding=[dp(8), 0])
                card_bg(box, (0.20, 0.06, 0.06, 1), radius=dp(8))
                box.add_widget(make_label(f"  {a['nom']}", color=Theme.get("TEXT"), size=FS_SMALL))
                box.add_widget(make_label(
                    f"{a['stock_actuel']} / min {a['stock_min']} {a['unite']}",
                    color=C_ORANGE, halign="right", size=FS_SMALL
                ))
                self.content.add_widget(box)

        # Dernieres commandes
        self.content.add_widget(make_label(
            "Dernieres commandes", bold=True, color=C_ACCENT, size=FS_HEAD
        ))
        commandes = db.get_commandes(date_debut=self._date_debut, date_fin=self._date_fin)
        if not commandes:
            self.content.add_widget(
                make_label("Aucune commande sur cette periode.",
                           color=Theme.get("MUTED"), size=FS_SMALL)
            )
        for c in commandes[:10]:
            total = db.get_total_commande(c["id"])
            self.content.add_widget(self._commande_row(c, total))

    def _kpi(self, label, value, color):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        card_bg(box, Theme.get("CARD"), radius=dp(14))
        box.add_widget(make_label(value, size=FS_KPI, bold=True, color=color, halign="center"))
        box.add_widget(make_label(label, size=FS_MICRO, color=Theme.get("MUTED"), halign="center"))
        return box

    def _commande_row(self, c, total):
        col = STATUT_COLORS.get(c["statut"], Theme.get("MUTED"))
        lbl = STATUT_LABELS.get(c["statut"], c["statut"])
        box = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8), padding=[dp(10), 0])
        card_bg(box, Theme.get("CARD"), radius=dp(10))
        box.add_widget(make_label(c["client"], size=FS_SMALL, bold=True))
        box.add_widget(make_label(lbl, size=FS_MICRO, color=col, halign="center"))
        box.add_widget(make_label(
            f"{total:,.0f} DA", size=FS_SMALL, color=C_GREEN, halign="right", bold=True
        ))
        return box


# ================================================================================
#  STOCK
# ================================================================================

class StockScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(name="stock", **kw)
        self._search = ""
        self._build()

    def _build(self):
        root = self.root_layout
        hdr = BoxLayout(size_hint_y=None, height=dp(58), padding=[dp(12), 4], spacing=dp(8))
        hdr.add_widget(make_label("Stock Ingredients", bold=True, size=FS_TITLE, color=C_ACCENT))
        hdr.add_widget(make_button("+ Ajouter", height=dp(42), on_press=self._popup_add,
                                   font_size=FS_SMALL))
        root.add_widget(hdr)

        search_box = BoxLayout(size_hint_y=None, height=dp(46), padding=[dp(10), 2])
        self._search_input = make_input("Rechercher un ingredient...", height=dp(42))
        self._search_input.bind(text=self._on_search)
        search_box.add_widget(self._search_input)
        root.add_widget(search_box)

        scroll = ScrollView()
        self.list_box = BoxLayout(
            orientation="vertical", spacing=dp(6),
            padding=[dp(10), 0, dp(10), dp(12)], size_hint_y=None
        )
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)

    def _on_search(self, inst, val):
        self._search = val.strip().lower()
        self.refresh()

    def refresh(self):
        self.list_box.clear_widgets()
        ings = db.get_ingredients()
        if self._search:
            ings = [i for i in ings if self._search in i["nom"].lower()]
        if not ings:
            self.list_box.add_widget(
                make_label("Aucun ingredient trouve.", color=Theme.get("MUTED"),
                           halign="center", size=FS_SMALL)
            )
        for ing in ings:
            self.list_box.add_widget(self._ing_row(ing))

    def _ing_row(self, ing):
        low = ing["stock_actuel"] <= ing["stock_min"]
        box = BoxLayout(size_hint_y=None, height=dp(68), spacing=dp(6), padding=[dp(10), 6])
        card_bg(box, Theme.get("CARD") if not low else (0.18, 0.08, 0.06, 1), radius=dp(12))

        info = BoxLayout(orientation="vertical")
        info.add_widget(make_label(ing["nom"], bold=True, size=FS_BODY))
        info.add_widget(make_label(
            f"Prix: {ing['prix_unitaire']} DA/{ing['unite']}",
            size=FS_MICRO, color=Theme.get("MUTED")
        ))
        info.add_widget(make_label(
            "⚠ STOCK FAIBLE" if low else "",
            size=FS_MICRO, color=C_RED
        ))
        box.add_widget(info)

        box.add_widget(make_label(
            f"{ing['stock_actuel']}\n{ing['unite']}",
            bold=True, color=C_RED if low else C_GREEN,
            halign="center", size=FS_BODY
        ))

        actions = BoxLayout(orientation="vertical", spacing=dp(4),
                            size_hint_x=None, width=dp(72))
        actions.add_widget(make_button(
            "Editer", height=dp(28), font_size=FS_MICRO,
            color=C_ACCENT2, text_color=Theme.get("TEXT"),
            on_press=lambda inst, i=ing: self._popup_edit(i)
        ))
        actions.add_widget(make_button(
            "Suppr.", height=dp(28), font_size=FS_MICRO,
            color=C_RED, text_color=Theme.get("TEXT"),
            on_press=lambda inst, i=ing: self._confirm_delete(i)
        ))
        box.add_widget(actions)
        return box

    def _popup_add(self, *a):
        self._popup_form()

    def _popup_edit(self, ing):
        self._popup_form(ing)

    def _popup_form(self, ing=None):
        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        content.add_widget(make_label("Nom", size=FS_SMALL, color=Theme.get("MUTED")))
        f_nom   = make_input("ex: Amandes")
        content.add_widget(f_nom)
        content.add_widget(make_label("Unite", size=FS_SMALL, color=Theme.get("MUTED")))
        f_unite = make_spinner(["kg", "g", "L", "ml", "unite"],
                               text=ing["unite"] if ing else "kg")
        content.add_widget(f_unite)
        content.add_widget(make_label("Stock actuel", size=FS_SMALL, color=Theme.get("MUTED")))
        f_stock = make_input("0", input_filter="float")
        content.add_widget(f_stock)
        content.add_widget(make_label("Stock minimum", size=FS_SMALL, color=Theme.get("MUTED")))
        f_min   = make_input("0", input_filter="float")
        content.add_widget(f_min)
        content.add_widget(make_label("Prix / unite (DA)", size=FS_SMALL, color=Theme.get("MUTED")))
        f_prix  = make_input("0", input_filter="float")
        content.add_widget(f_prix)

        if ing:
            f_nom.text   = ing["nom"]
            f_stock.text = str(ing["stock_actuel"])
            f_min.text   = str(ing["stock_min"])
            f_prix.text  = str(ing["prix_unitaire"])

        btn = make_button("Enregistrer", color=C_GREEN)
        content.add_widget(btn)

        scroll = ScrollView()
        scroll.add_widget(content)
        content.size_hint_y = None
        content.bind(minimum_height=content.setter("height"))

        pop = Popup(
            title="Modifier ingredient" if ing else "Nouvel ingredient",
            content=scroll, size_hint=(0.92, 0.85),
            background_color=Theme.get("BG"), title_color=C_ACCENT,
            title_size=FS_HEAD,
        )

        def _save(inst):
            try:
                nom = f_nom.text.strip()
                if not nom:
                    show_popup("Erreur", "Le nom est obligatoire", C_RED); return
                stock = float(f_stock.text or 0)
                smin  = float(f_min.text or 0)
                prix  = float(f_prix.text or 0)
                if ing:
                    db.update_ingredient(ing["id"], nom, f_unite.text, stock, smin, prix)
                else:
                    db.add_ingredient(nom, f_unite.text, stock, smin, prix)
                pop.dismiss()
                self.refresh()
                show_popup("OK", f"Ingredient '{nom}' enregistre.", C_GREEN)
            except Exception as e:
                show_popup("Erreur", str(e), C_RED)

        btn.bind(on_press=_save)
        pop.open()

    def _confirm_delete(self, ing):
        confirm_popup(
            "Supprimer",
            f"Supprimer '{ing['nom']}' ?\nSes recettes liees seront aussi supprimees.",
            lambda: self._do_delete(ing["id"])
        )

    def _do_delete(self, ing_id):
        try:
            db.delete_ingredient(ing_id)
            self.refresh()
        except Exception as e:
            show_popup("Erreur", str(e), C_RED)


# ================================================================================
#  ACHATS avec filtre de dates
# ================================================================================

class AchatsScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(name="achats", **kw)
        self._date_debut = None
        self._date_fin   = None
        self._build()

    def _build(self):
        root = self.root_layout
        hdr = BoxLayout(size_hint_y=None, height=dp(58), padding=[dp(12), 4], spacing=dp(8))
        hdr.add_widget(make_label("Achats / Reappro", bold=True, size=FS_TITLE, color=C_ACCENT))
        hdr.add_widget(make_button("+ Achat", height=dp(42), on_press=self._popup_achat,
                                   font_size=FS_SMALL))
        root.add_widget(hdr)

        self._filter_bar = DateFilterBar(
            on_change=self._on_date_change,
            padding=[dp(10), dp(2)],
        )
        root.add_widget(self._filter_bar)

        self._lbl_total = make_label("", size=FS_SMALL, color=C_ORANGE, halign="right",
                                     size_hint_y=None, height=dp(28))
        self._lbl_total.padding = [dp(16), 0]
        root.add_widget(self._lbl_total)

        scroll = ScrollView()
        self.list_box = BoxLayout(
            orientation="vertical", spacing=dp(6),
            padding=[dp(10), 0, dp(10), dp(12)], size_hint_y=None
        )
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)

    def _on_date_change(self, debut, fin):
        self._date_debut = debut
        self._date_fin   = fin
        self.refresh()

    def refresh(self):
        self.list_box.clear_widgets()
        achats = db.get_achats_history(self._date_debut, self._date_fin)
        total_dep = sum(a["prix_total"] for a in achats)
        self._lbl_total.text = f"Total depenses : {total_dep:,.0f} DA"

        if not achats:
            self.list_box.add_widget(
                make_label("Aucun achat sur cette periode.", color=Theme.get("MUTED"),
                           halign="center", size=FS_SMALL)
            )
            return

        for a in achats:
            box = BoxLayout(size_hint_y=None, height=dp(62), spacing=dp(6), padding=[dp(10), 6])
            card_bg(box, Theme.get("CARD"), radius=dp(12))

            info = BoxLayout(orientation="vertical")
            info.add_widget(make_label(a["ingredient_nom"], bold=True, size=FS_BODY))
            date = a["created_at"][:10] if a["created_at"] else ""
            info.add_widget(make_label(
                f"{a['fournisseur'] or 'Fournisseur'}  |  {date}",
                size=FS_MICRO, color=Theme.get("MUTED")
            ))
            box.add_widget(info)
            box.add_widget(make_label(
                f"+{a['quantite']} {a['unite']}",
                color=C_GREEN, halign="center", bold=True, size=FS_SMALL
            ))
            box.add_widget(make_label(
                f"{a['prix_total']:,.0f} DA",
                color=C_ACCENT, halign="right", bold=True, size=FS_SMALL
            ))
            self.list_box.add_widget(box)

    def _popup_achat(self, *a):
        ings = db.get_ingredients()
        if not ings:
            show_popup("Info", "Ajoutez d'abord des ingredients.", C_ORANGE); return

        ing_names = [i["nom"] for i in ings]
        ing_map   = {i["nom"]: i for i in ings}

        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        content.add_widget(make_label("Ingredient", size=FS_SMALL, color=Theme.get("MUTED")))
        sp_ing = make_spinner(ing_names)
        content.add_widget(sp_ing)
        content.add_widget(make_label("Quantite achetee", size=FS_SMALL, color=Theme.get("MUTED")))
        f_qte  = make_input("0", input_filter="float")
        content.add_widget(f_qte)
        content.add_widget(make_label("Prix total (DA)", size=FS_SMALL, color=Theme.get("MUTED")))
        f_prix = make_input("0", input_filter="float")
        content.add_widget(f_prix)
        content.add_widget(make_label("Fournisseur (optionnel)", size=FS_SMALL, color=Theme.get("MUTED")))
        f_four = make_input("ex: Marche central")
        content.add_widget(f_four)

        btn = make_button("Enregistrer l'achat", color=C_GREEN)
        content.add_widget(btn)

        scroll = ScrollView()
        scroll.add_widget(content)
        content.size_hint_y = None
        content.bind(minimum_height=content.setter("height"))

        pop = Popup(title="Nouvel achat", content=scroll, size_hint=(0.92, 0.85),
                    background_color=Theme.get("BG"), title_color=C_ACCENT, title_size=FS_HEAD)

        def _save(inst):
            try:
                ing  = ing_map[sp_ing.text]
                qte  = float(f_qte.text or 0)
                prix = float(f_prix.text or 0)
                if qte <= 0:
                    show_popup("Erreur", "Quantite invalide (doit etre > 0)", C_RED); return
                db.add_achat(ing["id"], qte, prix, f_four.text.strip())
                pop.dismiss()
                self.refresh()
                show_popup("Achat enregistre", f"{ing['nom']} : +{qte} {ing['unite']}", C_GREEN)
            except Exception as e:
                show_popup("Erreur", str(e), C_RED)

        btn.bind(on_press=_save)
        pop.open()


# ================================================================================
#  PRODUITS + RECETTES
# ================================================================================

class ProduitsScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(name="produits", **kw)
        self._build()

    def _build(self):
        root = self.root_layout
        hdr = BoxLayout(size_hint_y=None, height=dp(58), padding=[dp(12), 4], spacing=dp(8))
        hdr.add_widget(make_label("Produits & Recettes", bold=True, size=FS_TITLE, color=C_ACCENT))
        hdr.add_widget(make_button("+ Produit", height=dp(42), on_press=self._popup_add,
                                   font_size=FS_SMALL))
        root.add_widget(hdr)
        scroll = ScrollView()
        self.list_box = BoxLayout(
            orientation="vertical", spacing=dp(8),
            padding=[dp(10), 0, dp(10), dp(12)], size_hint_y=None
        )
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)

    def refresh(self):
        self.list_box.clear_widgets()
        produits = db.get_produits()
        if not produits:
            self.list_box.add_widget(
                make_label("Aucun produit. Appuyez sur + Produit.", color=Theme.get("MUTED"),
                           halign="center", size=FS_SMALL)
            )
        for p in produits:
            self.list_box.add_widget(self._prod_row(p))

    def _prod_row(self, p):
        recette  = db.get_recette(p["id"])
        nb_ings  = len(recette)
        box = BoxLayout(size_hint_y=None, height=dp(74), spacing=dp(6), padding=[dp(10), 6])
        card_bg(box, Theme.get("CARD"), radius=dp(12))

        info = BoxLayout(orientation="vertical")
        info.add_widget(make_label(p["nom"], bold=True, size=FS_BODY))
        info.add_widget(make_label(p["description"] or "", size=FS_MICRO, color=Theme.get("MUTED")))
        rec_color = C_ORANGE if nb_ings == 0 else Theme.get("MUTED")
        rec_txt   = "⚠ Recette vide" if nb_ings == 0 else f"{nb_ings} ingredient(s)"
        info.add_widget(make_label(rec_txt, size=FS_MICRO, color=rec_color))
        box.add_widget(info)

        box.add_widget(make_label(
            f"{p['prix_vente']:,.0f} DA\n/ piece",
            color=C_GREEN, halign="center", bold=True, size=FS_SMALL
        ))

        actions = BoxLayout(orientation="vertical", spacing=dp(4),
                            size_hint_x=None, width=dp(76))
        actions.add_widget(make_button(
            "Recette", height=dp(30), font_size=FS_MICRO,
            color=C_ACCENT2, text_color=Theme.get("TEXT"),
            on_press=lambda inst, pp=p: self._popup_recette(pp)
        ))
        actions.add_widget(make_button(
            "Editer", height=dp(30), font_size=FS_MICRO,
            color=C_ACCENT, text_color=(0, 0, 0, 1),
            on_press=lambda inst, pp=p: self._popup_form(pp)
        ))
        box.add_widget(actions)
        return box

    def _popup_add(self, *a):
        self._popup_form()

    def _popup_form(self, p=None):
        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        content.add_widget(make_label("Nom du produit", size=FS_SMALL, color=Theme.get("MUTED")))
        f_nom  = make_input("ex: Baklawa")
        content.add_widget(f_nom)
        content.add_widget(make_label("Prix / piece (DA)", size=FS_SMALL, color=Theme.get("MUTED")))
        f_prix = make_input("0", input_filter="float")
        content.add_widget(f_prix)
        content.add_widget(make_label("Description (optionnel)", size=FS_SMALL, color=Theme.get("MUTED")))
        f_desc = make_input("ex: Baklawa classique aux amandes")
        content.add_widget(f_desc)

        if p:
            f_nom.text  = p["nom"]
            f_prix.text = str(p["prix_vente"])
            f_desc.text = p["description"] or ""

        btn_save = make_button("Enregistrer", color=C_GREEN)
        content.add_widget(btn_save)
        if p:
            btn_del = make_button("Supprimer ce produit", color=C_RED,
                                  text_color=Theme.get("TEXT"))
            content.add_widget(btn_del)

        scroll = ScrollView()
        scroll.add_widget(content)
        content.size_hint_y = None
        content.bind(minimum_height=content.setter("height"))

        pop = Popup(
            title="Modifier produit" if p else "Nouveau produit",
            content=scroll, size_hint=(0.92, 0.75),
            background_color=Theme.get("BG"), title_color=C_ACCENT, title_size=FS_HEAD,
        )

        def _save(inst):
            try:
                nom = f_nom.text.strip()
                if not nom:
                    show_popup("Erreur", "Nom obligatoire", C_RED); return
                prix = float(f_prix.text or 0)
                if p:
                    db.update_produit(p["id"], nom, prix, f_desc.text.strip())
                else:
                    db.add_produit(nom, prix, f_desc.text.strip())
                pop.dismiss()
                self.refresh()
            except Exception as e:
                show_popup("Erreur", str(e), C_RED)

        btn_save.bind(on_press=_save)
        if p:
            btn_del.bind(on_press=lambda inst: (
                pop.dismiss(),
                confirm_popup(
                    "Supprimer",
                    f"Supprimer '{p['nom']}' ?\nSes recettes seront supprimees.",
                    lambda: (db.delete_produit(p["id"]), self.refresh())
                )
            ))
        pop.open()

    def _popup_recette(self, p):
        ings    = db.get_ingredients()
        recette = db.get_recette(p["id"])
        rec_map = {r["ingredient_id"]: r for r in recette}

        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        content.add_widget(make_label(
            f"Recette : {p['nom']}", bold=True, size=FS_HEAD, color=C_ACCENT
        ))
        content.add_widget(make_label(
            "Quantites pour 100 pieces. Mettre 0 pour exclure.",
            size=FS_MICRO, color=Theme.get("MUTED")
        ))

        hdr = BoxLayout(size_hint_y=None, height=dp(28))
        hdr.add_widget(make_label("Ingredient", size=FS_MICRO, color=Theme.get("MUTED")))
        hdr.add_widget(make_label("Qte / 100 pcs", size=FS_MICRO,
                                  color=Theme.get("MUTED"), halign="right"))
        content.add_widget(hdr)

        fields = {}
        for ing in ings:
            row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
            row.add_widget(make_label(f"{ing['nom']} ({ing['unite']})", size=FS_SMALL))
            fi = make_input("0", input_filter="float", height=dp(40))
            fi.size_hint_x = 0.32
            existing = rec_map.get(ing["id"])
            fi.text = str(existing["quantite_100"]) if existing else "0"
            row.add_widget(fi)
            fields[ing["id"]] = fi
            content.add_widget(row)

        btn_save = make_button("Enregistrer la recette", color=C_GREEN)
        content.add_widget(btn_save)

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(content)
        content.size_hint_y = None
        content.bind(minimum_height=content.setter("height"))

        pop = Popup(
            title=f"Recette - {p['nom']}",
            content=scroll, size_hint=(0.94, 0.90),
            background_color=Theme.get("BG"), title_color=C_ACCENT, title_size=FS_HEAD,
        )

        def _save(inst):
            try:
                for ing_id, fi in fields.items():
                    db.set_recette_ligne(p["id"], ing_id, float(fi.text or 0))
                pop.dismiss()
                self.refresh()
                show_popup("OK", f"Recette de {p['nom']} enregistree", C_GREEN)
            except Exception as e:
                show_popup("Erreur", str(e), C_RED)

        btn_save.bind(on_press=_save)
        pop.open()


# ================================================================================
#  COMMANDES  —  statuts : en_cours / terminee
# ================================================================================

class CommandesScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(name="commandes", **kw)
        self._filter_statut = None
        self._date_debut    = None
        self._date_fin      = None
        self._build()

    def _build(self):
        root = self.root_layout

        hdr = BoxLayout(size_hint_y=None, height=dp(58), padding=[dp(12), 4], spacing=dp(8))
        hdr.add_widget(make_label("Commandes", bold=True, size=FS_TITLE, color=C_ACCENT))
        hdr.add_widget(make_button("+ Commande", height=dp(42), on_press=self._popup_new,
                                   font_size=FS_SMALL))
        root.add_widget(hdr)

        # Filtre statut (3 boutons seulement)
        filters = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6),
                            padding=[dp(10), 0])
        for key, lbl in [("all", "Tout"), ("en_cours", "En cours"), ("terminee", "Terminee")]:
            btn = make_button(lbl, height=dp(36), font_size=FS_MICRO,
                              color=C_ACCENT if key == "all" else Theme.get("CARD"),
                              text_color=(0, 0, 0, 1) if key == "all" else Theme.get("TEXT"))
            btn.bind(on_press=lambda inst, k=key: self._set_statut(k))
            filters.add_widget(btn)
        root.add_widget(filters)

        self._filter_bar = DateFilterBar(
            on_change=self._on_date_change,
            padding=[dp(10), dp(2)],
        )
        root.add_widget(self._filter_bar)

        self._lbl_resume = make_label(
            "", size=FS_SMALL, color=Theme.get("MUTED"), halign="center",
            size_hint_y=None, height=dp(24)
        )
        root.add_widget(self._lbl_resume)

        scroll = ScrollView()
        self.list_box = BoxLayout(
            orientation="vertical", spacing=dp(6),
            padding=[dp(10), dp(4), dp(10), dp(16)], size_hint_y=None
        )
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)

    def _set_statut(self, key):
        self._filter_statut = None if key == "all" else key
        self.refresh()

    def _on_date_change(self, debut, fin):
        self._date_debut = debut
        self._date_fin   = fin
        self.refresh()

    def refresh(self):
        self.list_box.clear_widgets()
        commandes = db.get_commandes(
            statut=self._filter_statut,
            date_debut=self._date_debut,
            date_fin=self._date_fin,
        )
        total_ca = sum(db.get_total_commande(c["id"]) for c in commandes)
        self._lbl_resume.text = (
            f"{len(commandes)} commande(s)  |  CA : {total_ca:,.0f} DA"
            if commandes else "Aucune commande sur cette periode."
        )

        if not commandes:
            self.list_box.add_widget(
                make_label("Aucune commande.", color=Theme.get("MUTED"),
                           halign="center", size=FS_SMALL)
            )
        for c in commandes:
            total = db.get_total_commande(c["id"])
            self.list_box.add_widget(self._cmd_row(c, total))

    def _cmd_row(self, c, total):
        col = STATUT_COLORS.get(c["statut"], Theme.get("MUTED"))
        box = BoxLayout(size_hint_y=None, height=dp(78), spacing=dp(6), padding=[dp(10), 6])
        card_bg(box, Theme.get("CARD"), radius=dp(12))

        info = BoxLayout(orientation="vertical", size_hint_x=0.42)
        info.add_widget(make_label(c["client"], bold=True, size=FS_BODY))
        info.add_widget(make_label(c["telephone"] or "", size=FS_MICRO, color=Theme.get("MUTED")))
        info.add_widget(make_label(
            f"Livr: {c['date_livraison'] or '-'}", size=FS_MICRO, color=Theme.get("MUTED")
        ))
        box.add_widget(info)

        mid = BoxLayout(orientation="vertical", size_hint_x=0.30)
        mid.add_widget(make_label(
            STATUT_LABELS.get(c["statut"], c["statut"]),
            size=FS_MICRO, color=col, halign="center", bold=True
        ))
        mid.add_widget(make_label(
            f"{total:,.0f} DA", bold=True, color=C_GREEN, halign="center", size=FS_SMALL
        ))
        mid.add_widget(make_label(
            c["created_at"][:10] if c["created_at"] else "",
            size=FS_MICRO, color=Theme.get("MUTED"), halign="center"
        ))
        box.add_widget(mid)

        act = BoxLayout(orientation="vertical", spacing=dp(4),
                        size_hint_x=None, width=dp(76))
        act.add_widget(make_button(
            "Detail", height=dp(30), font_size=FS_MICRO,
            color=C_ACCENT2, text_color=Theme.get("TEXT"),
            on_press=lambda inst, cc=c: self._popup_detail(cc)
        ))
        act.add_widget(make_button(
            "Statut", height=dp(30), font_size=FS_MICRO,
            color=C_ACCENT, text_color=(0, 0, 0, 1),
            on_press=lambda inst, cc=c: self._popup_statut(cc)
        ))
        box.add_widget(act)
        return box

    def _popup_detail(self, c):
        commande, lignes = db.get_commande_detail(c["id"])
        besoins  = db.get_besoin_stock_pour_commande(c["id"])
        tout_ok  = all(b["ok"] for b in besoins)

        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))

        cli_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(72),
                            padding=[dp(12), dp(8)], spacing=dp(6))
        card_bg(cli_box, Theme.get("CARD2"), radius=dp(12))
        cli_box.add_widget(make_label(f"Client : {c['client']}", bold=True, size=FS_BODY))
        cli_box.add_widget(make_label(
            f"Tel : {c['telephone'] or '-'}   |   Livraison : {c['date_livraison'] or '-'}",
            size=FS_SMALL, color=Theme.get("MUTED")
        ))
        content.add_widget(cli_box)

        if c["notes"]:
            content.add_widget(make_label(
                f"Notes : {c['notes']}", size=FS_SMALL, color=Theme.get("MUTED")
            ))

        content.add_widget(make_label(
            "PRODUITS COMMANDES :", bold=True, size=FS_SMALL, color=C_ACCENT
        ))

        total = 0
        for l in lignes:
            sous_total = l["nb_pieces"] * l["prix_unitaire"]
            total += sous_total
            row = BoxLayout(size_hint_y=None, height=dp(52),
                            padding=[dp(12), dp(6)], spacing=dp(8))
            card_bg(row, Theme.get("CARD"), radius=dp(10))
            row.add_widget(make_label(l["produit_nom"], bold=True, size=FS_BODY))
            row.add_widget(make_label(f"{int(l['nb_pieces'])} pcs",
                                      size=FS_SMALL, color=Theme.get("MUTED"), halign="center"))
            row.add_widget(make_label(f"{sous_total:,.0f} DA",
                                      bold=True, color=C_GREEN, halign="right", size=FS_BODY))
            content.add_widget(row)

        tot_box = BoxLayout(size_hint_y=None, height=dp(54), padding=[dp(12), dp(8)])
        card_bg(tot_box, (0.06, 0.20, 0.10, 1), radius=dp(12))
        tot_box.add_widget(make_label("TOTAL", bold=True, size=FS_BODY, color=Theme.get("MUTED")))
        tot_box.add_widget(make_label(
            f"{total:,.0f} DA", bold=True, color=C_GREEN, halign="right", size=FS_TITLE
        ))
        content.add_widget(tot_box)

        if besoins:
            bilan_col = C_GREEN if tout_ok else C_ORANGE
            content.add_widget(make_label(
                f"BILAN INGREDIENTS : {'✓ OK' if tout_ok else '⚠ MANQUES !'}",
                bold=True, size=FS_SMALL, color=bilan_col
            ))
            for b in besoins:
                row = BoxLayout(size_hint_y=None, height=dp(32), padding=[dp(6), 0])
                row.add_widget(make_label(b["nom"], size=FS_SMALL))
                if b["ok"]:
                    row.add_widget(make_label(
                        f"{b['besoin']:.3f} {b['unite']} ✓",
                        size=FS_SMALL, color=C_GREEN, halign="right"
                    ))
                else:
                    row.add_widget(make_label(
                        f"besoin {b['besoin']:.3f} | manque {b['manque']:.3f} {b['unite']}",
                        size=FS_MICRO, color=C_RED, halign="right"
                    ))
                content.add_widget(row)

        row_btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_close = make_button("Fermer",    color=Theme.get("MUTED"), text_color=Theme.get("TEXT"))
        btn_del   = make_button("Supprimer", color=C_RED,   text_color=Theme.get("TEXT"))
        row_btns.add_widget(btn_close)
        row_btns.add_widget(btn_del)
        content.add_widget(row_btns)

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(content)
        content.size_hint_y = None
        content.bind(minimum_height=content.setter("height"))

        pop = Popup(
            title=f"Commande #{c['id']}  —  {c['client']}",
            content=scroll, size_hint=(0.96, 0.92),
            background_color=Theme.get("BG"), title_color=C_ACCENT, title_size=FS_HEAD,
        )
        btn_close.bind(on_press=pop.dismiss)

        def _del_commande():
            db.delete_commande(c["id"])
            self.refresh()

        btn_del.bind(on_press=lambda inst: (
            pop.dismiss(),
            confirm_popup(
                "Supprimer",
                "Supprimer cette commande ?\n(Le stock sera restaure si elle etait terminee.)",
                _del_commande
            )
        ))
        pop.open()

    def _popup_statut(self, c):
        besoins = db.get_besoin_stock_pour_commande(c["id"])
        manques = [b for b in besoins if not b["ok"]]

        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))

        if manques and c["statut"] != "terminee":
            content.add_widget(make_label(
                "Stock insuffisant :", bold=True, color=C_RED, size=FS_SMALL
            ))
            for m in manques:
                content.add_widget(make_label(
                    f"  - {m['nom']} : manque {m['manque']:.3f} {m['unite']}",
                    size=FS_SMALL, color=C_ORANGE
                ))
            content.add_widget(make_label(
                "Vous pouvez quand meme marquer comme terminee.",
                size=FS_MICRO, color=Theme.get("MUTED")
            ))

        content.add_widget(make_label("Changer le statut :", bold=True, size=FS_BODY))

        pop = Popup(title="Statut commande", content=content,
                    size_hint=(0.90, 0.60), background_color=Theme.get("BG"),
                    title_color=C_ACCENT, title_size=FS_HEAD)

        # Seulement 2 statuts
        for s in ["en_cours", "terminee"]:
            col = STATUT_COLORS[s]
            tc  = (0, 0, 0, 1) if s == "terminee" else Theme.get("TEXT")
            btn = make_button(STATUT_LABELS[s], color=col, text_color=tc, height=dp(52))
            btn.bind(on_press=lambda inst, ss=s: (
                db.update_statut_commande(c["id"], ss),
                pop.dismiss(), self.refresh()
            ))
            content.add_widget(btn)

        content.add_widget(make_button(
            "Annuler", color=Theme.get("MUTED"), height=dp(44),
            text_color=Theme.get("TEXT"),
            on_press=lambda inst: pop.dismiss()
        ))
        pop.open()

    def _popup_new(self, *a):
        produits = db.get_produits()
        if not produits:
            show_popup("Info", "Ajoutez d'abord des produits.", C_ORANGE); return

        prod_names = [p["nom"] for p in produits]
        prod_map   = {p["nom"]: p for p in produits}

        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))

        content.add_widget(make_label("Nom du client *", size=FS_SMALL, color=Theme.get("MUTED")))
        f_client = make_input("ex: Fatima Benali")
        content.add_widget(f_client)

        content.add_widget(make_label("Telephone", size=FS_SMALL, color=Theme.get("MUTED")))
        f_tel = make_input("ex: 0555 123 456")
        content.add_widget(f_tel)

        content.add_widget(make_label("Date livraison", size=FS_SMALL, color=Theme.get("MUTED")))
        f_date = make_input(f"ex: {datetime.now().strftime('%d/%m/%Y')}")
        content.add_widget(f_date)

        content.add_widget(make_label("Notes", size=FS_SMALL, color=Theme.get("MUTED")))
        f_notes = make_input("ex: Sans sucre")
        content.add_widget(f_notes)

        content.add_widget(make_label(
            "Produits  (Produit | Nb pieces | Prix DA/pce)",
            size=FS_SMALL, color=C_ACCENT, bold=True
        ))

        lignes_widgets = []

        def add_ligne(*a):
            row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
            sp = make_spinner(prod_names)
            sp.size_hint_x = 0.46
            fq = make_input("Qte", input_filter="int", height=dp(44))
            fq.size_hint_x = 0.20
            fp = make_input("Prix", input_filter="float", height=dp(44))
            fp.size_hint_x = 0.34
            def _auto(inst, val, _fp=fp):
                if val in prod_map:
                    _fp.text = str(prod_map[val]["prix_vente"])
            sp.bind(text=_auto)
            fp.text = str(prod_map[prod_names[0]]["prix_vente"])
            row.add_widget(sp); row.add_widget(fq); row.add_widget(fp)
            lignes_widgets.append((sp, fq, fp))
            content.add_widget(row)

        add_ligne()
        content.add_widget(make_button(
            "+ Ajouter produit", height=dp(40),
            color=Theme.get("CARD2"), text_color=Theme.get("TEXT"),
            font_size=FS_SMALL, on_press=add_ligne
        ))
        btn_save = make_button("Enregistrer la commande", color=C_GREEN)
        content.add_widget(btn_save)

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(content)
        content.size_hint_y = None
        content.bind(minimum_height=content.setter("height"))

        pop = Popup(title="Nouvelle commande", content=scroll,
                    size_hint=(0.95, 0.92), background_color=Theme.get("BG"),
                    title_color=C_ACCENT, title_size=FS_HEAD)

        def _save(inst):
            try:
                client = f_client.text.strip()
                if not client:
                    show_popup("Erreur", "Nom du client obligatoire", C_RED); return
                lignes = []
                for sp, fq, fp in lignes_widgets:
                    nb   = int(float(fq.text or 0))
                    prix = float(fp.text or 0)
                    if nb > 0:
                        lignes.append((prod_map[sp.text]["id"], nb, prix))
                if not lignes:
                    show_popup("Erreur", "Ajoutez au moins un produit (qte > 0)", C_RED); return
                db.add_commande(client, f_tel.text.strip(), f_date.text.strip(),
                                f_notes.text.strip(), lignes)
                pop.dismiss()
                self.refresh()
                show_popup("Commande creee", f"Client : {client}", C_GREEN)
            except Exception as e:
                show_popup("Erreur", str(e), C_RED)

        btn_save.bind(on_press=_save)
        pop.open()


# ================================================================================
#  PARAMETRES  —  avec toggle Dark / Light
# ================================================================================

class ParamsScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(name="params", **kw)
        self._build()

    def _build(self):
        root = self.root_layout
        hdr = BoxLayout(size_hint_y=None, height=dp(58), padding=[dp(12), 4])
        hdr.add_widget(make_label(
            "Parametres & Sauvegarde", bold=True, size=FS_TITLE, color=C_ACCENT
        ))
        root.add_widget(hdr)
        scroll = ScrollView()
        self.content = BoxLayout(
            orientation="vertical", spacing=dp(12),
            padding=[dp(12), dp(8), dp(12), dp(16)], size_hint_y=None
        )
        self.content.bind(minimum_height=self.content.setter("height"))
        scroll.add_widget(self.content)
        root.add_widget(scroll)

    def refresh(self):
        self.content.clear_widgets()
        c = self.content

        # ── THEME ─────────────────────────────────────────
        c.add_widget(make_label("THEME", bold=True, size=FS_SMALL, color=C_ACCENT))

        theme_row = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(10),
                              padding=[dp(0), dp(4)])

        lbl_mode = make_label(
            "🌙 Mode sombre" if Theme.is_dark() else "☀  Mode clair",
            size=FS_BODY, bold=True, color=Theme.get("TEXT")
        )
        theme_row.add_widget(lbl_mode)

        toggle_color = C_ACCENT2 if Theme.is_dark() else C_ORANGE
        toggle_text  = "Passer en clair ☀" if Theme.is_dark() else "Passer en sombre 🌙"
        btn_toggle = make_button(toggle_text, color=toggle_color,
                                 text_color=Theme.get("TEXT"), height=dp(46),
                                 font_size=FS_SMALL)

        def _toggle(inst):
            Theme.set_dark(not Theme.is_dark())
            # Rafraichir la barre de nav
            if hasattr(self, "navbar"):
                self.navbar.apply_theme()
            self.refresh()

        btn_toggle.bind(on_press=_toggle)
        theme_row.add_widget(btn_toggle)
        c.add_widget(theme_row)

        # Apercu palette
        pal_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
        for col, name in [
            (Theme.get("BG"),    "BG"),
            (Theme.get("CARD"),  "Card"),
            (Theme.get("TEXT"),  "Texte"),
            (C_ACCENT,           "Accent"),
            (C_GREEN,            "Vert"),
        ]:
            swatch = Widget(size_hint_x=1)
            with swatch.canvas:
                Color(*col)
                rr = RoundedRectangle(pos=swatch.pos, size=swatch.size, radius=[dp(6)])
            swatch.bind(pos=lambda o, v, _r=rr: setattr(_r, "pos", v))
            swatch.bind(size=lambda o, v, _r=rr: setattr(_r, "size", v))
            pal_row.add_widget(swatch)
        c.add_widget(pal_row)

        # ── BASE DE DONNEES ────────────────────────────────
        c.add_widget(make_label("BASE DE DONNEES", bold=True, size=FS_SMALL, color=C_ACCENT))

        path_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(68),
                             padding=[dp(12), dp(10)], spacing=dp(6))
        card_bg(path_box, Theme.get("CARD"), radius=dp(12))
        path_box.add_widget(make_label("Chemin actuel :", size=FS_MICRO,
                                       color=Theme.get("MUTED")))
        path_box.add_widget(make_label(db.get_db_path(), size=FS_SMALL,
                                       color=Theme.get("TEXT"), bold=True))
        c.add_widget(path_box)

        c.add_widget(make_label("Changer le chemin :", size=FS_SMALL,
                                color=Theme.get("MUTED")))
        self.f_path = make_input("ex: /sdcard/Patisserie/data.db")
        c.add_widget(self.f_path)
        c.add_widget(make_button(
            "Appliquer le chemin", color=C_ACCENT2,
            text_color=Theme.get("TEXT"), height=dp(48),
            on_press=self._change_path
        ))

        # ── SAUVEGARDE ─────────────────────────────────────
        c.add_widget(make_label("SAUVEGARDE", bold=True, size=FS_SMALL, color=C_ACCENT))
        c.add_widget(make_button(
            "Creer une sauvegarde maintenant", color=C_GREEN,
            height=dp(52), on_press=self._do_backup
        ))

        backups = db.list_backups()
        if backups:
            c.add_widget(make_label(
                f"Sauvegardes disponibles ({len(backups)}) :",
                size=FS_SMALL, color=Theme.get("MUTED")
            ))
            for bk in backups[:8]:
                row = BoxLayout(size_hint_y=None, height=dp(60),
                                spacing=dp(8), padding=[dp(10), dp(6)])
                card_bg(row, Theme.get("CARD"), radius=dp(12))
                info = BoxLayout(orientation="vertical")
                info.add_widget(make_label(
                    bk["name"].replace("patisserie_backup_", "backup_"),
                    size=FS_SMALL, bold=True
                ))
                info.add_widget(make_label(
                    f"{bk['size'] // 1024} Ko", size=FS_MICRO, color=Theme.get("MUTED")
                ))
                row.add_widget(info)
                row.add_widget(make_button(
                    "Restaurer", height=dp(38), font_size=FS_SMALL,
                    color=C_ORANGE, text_color=(0, 0, 0, 1),
                    on_press=lambda inst, b=bk: self._confirm_restore(b)
                ))
                c.add_widget(row)
        else:
            c.add_widget(make_label("Aucune sauvegarde.", size=FS_SMALL,
                                    color=Theme.get("MUTED")))

    def _change_path(self, *a):
        path = self.f_path.text.strip()
        if not path:
            show_popup("Erreur", "Entrez un chemin valide", C_RED); return
        try:
            db.set_db_path(path)
            db.init_db()
            self.f_path.text = ""
            self.refresh()
            show_popup("OK", "Chemin mis a jour", C_GREEN)
        except Exception as e:
            show_popup("Erreur", str(e), C_RED)

    def _do_backup(self, *a):
        try:
            path = db.backup_db()
            self.refresh()
            show_popup("Sauvegarde OK", f"Fichier : {os.path.basename(path)}", C_GREEN)
        except Exception as e:
            show_popup("Erreur", str(e), C_RED)

    def _confirm_restore(self, bk):
        confirm_popup(
            "Restaurer",
            f"Restaurer '{bk['name']}' ?\nLes donnees actuelles seront remplacees.",
            lambda: self._do_restore(bk)
        )

    def _do_restore(self, bk):
        try:
            db.restore_db(bk["path"])
            self.refresh()
            show_popup("Restauration OK", "Base de donnees restauree.", C_GREEN)
        except Exception as e:
            show_popup("Erreur", str(e), C_RED)


# ================================================================================
#  APP
# ================================================================================

class PatisserieApp(App):
    def build(self):
        db.init_db()
        Window.softinput_mode = "below_target"

        sm = ScreenManager(transition=SlideTransition(duration=0.18))
        screens = [
            DashboardScreen(),
            StockScreen(),
            AchatsScreen(),
            ProduitsScreen(),
            CommandesScreen(),
            ParamsScreen(),
        ]

        main   = BoxLayout(orientation="vertical")
        navbar = NavBar(sm)

        for scr in screens:
            scr.set_navbar(navbar)
            sm.add_widget(scr)

        main.add_widget(sm)
        main.add_widget(navbar)
        sm.current = "dashboard"
        navbar.highlight("dashboard")
        return main

    def get_application_name(self):
        return "Patisserie Orientale"


if __name__ == "__main__":
    PatisserieApp().run()