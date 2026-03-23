"""
Base de données — Patisserie Orientale
- DB_PATH configurable (Android: dossier externe)
- Backup / Restore
- Recettes kg/100 pieces
- Deduction stock automatique a la livraison
- Filtres par date / semaine / mois
"""

import sqlite3
import shutil
import os
from datetime import datetime, timedelta

# ── Chemin DB ────────────────────────────────────────
def _get_db_dir():
    sdcard = "/sdcard/Patisserie"
    if os.path.exists("/sdcard"):
        os.makedirs(sdcard, exist_ok=True)
        return sdcard
    return os.path.dirname(os.path.abspath(__file__))

DB_DIR  = _get_db_dir()
DB_PATH = os.path.join(DB_DIR, "patisserie.db")


def set_db_path(path):
    global DB_PATH
    DB_PATH = path

def get_db_path():
    return DB_PATH

def backup_db(dest_path=None):
    if dest_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_path = os.path.join(DB_DIR, f"patisserie_backup_{ts}.db")
    shutil.copy2(DB_PATH, dest_path)
    return dest_path

def restore_db(source_path):
    shutil.copy2(source_path, DB_PATH)

def list_backups():
    files = []
    for f in os.listdir(DB_DIR):
        if f.startswith("patisserie_backup_") and f.endswith(".db"):
            full = os.path.join(DB_DIR, f)
            size = os.path.getsize(full)
            files.append({"name": f, "path": full, "size": size})
    return sorted(files, key=lambda x: x["name"], reverse=True)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            nom           TEXT    NOT NULL UNIQUE,
            unite         TEXT    NOT NULL DEFAULT 'kg',
            stock_actuel  REAL    NOT NULL DEFAULT 0,
            stock_min     REAL    NOT NULL DEFAULT 0,
            prix_unitaire REAL    NOT NULL DEFAULT 0,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS produits (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nom         TEXT    NOT NULL UNIQUE,
            prix_vente  REAL    NOT NULL DEFAULT 0,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS recettes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            produit_id      INTEGER NOT NULL REFERENCES produits(id)    ON DELETE CASCADE,
            ingredient_id   INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
            quantite_100    REAL    NOT NULL DEFAULT 0,
            UNIQUE(produit_id, ingredient_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS commandes (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            client         TEXT    NOT NULL,
            telephone      TEXT,
            statut         TEXT    NOT NULL DEFAULT 'en_attente',
            stock_deduit   INTEGER NOT NULL DEFAULT 0,
            date_livraison TEXT,
            notes          TEXT,
            created_at     TEXT    DEFAULT (datetime('now'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS commande_lignes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            commande_id   INTEGER NOT NULL REFERENCES commandes(id) ON DELETE CASCADE,
            produit_id    INTEGER NOT NULL REFERENCES produits(id),
            nb_pieces     REAL    NOT NULL DEFAULT 1,
            prix_unitaire REAL    NOT NULL DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS achats (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
            quantite      REAL    NOT NULL,
            prix_total    REAL    NOT NULL DEFAULT 0,
            fournisseur   TEXT,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    _seed_demo_data(conn)
    conn.close()


def _seed_demo_data(conn):
    c = conn.cursor()
    # Ne rien inserer si des donnees existent deja (ingredients OU produits)
    c.execute("SELECT COUNT(*) FROM ingredients")
    if c.fetchone()[0] > 0:
        return
    c.execute("SELECT COUNT(*) FROM produits")
    if c.fetchone()[0] > 0:
        return
    ingredients = [
        ("Amandes",     "kg", 8.0, 2.0, 1500),
        ("Pistaches",   "kg", 3.0, 1.0, 2500),
        ("Noix",        "kg", 5.0, 1.0, 1200),
        ("Sucre",       "kg",20.0, 5.0,  150),
        ("Farine",      "kg",15.0, 5.0,   80),
        ("Beurre",      "kg", 6.0, 2.0,  900),
        ("Miel",        "kg", 4.0, 1.0,  800),
        ("Eau de fleur","L",  2.0, 0.5,  300),
        ("Semoule",     "kg",10.0, 3.0,   90),
    ]
    c.executemany(
        "INSERT INTO ingredients(nom,unite,stock_actuel,stock_min,prix_unitaire) VALUES(?,?,?,?,?)",
        ingredients
    )
    produits = [
        ("Baklawa",        35, "Baklawa classique aux amandes"),
        ("Dziziat",        40, "Dziziat aux pistaches"),
        ("Tcharak",        30, "Tcharak au beurre"),
        ("Makrout Amande", 25, "Makrout aux amandes"),
        ("Griwech",        15, "Griwech au miel"),
    ]
    c.executemany(
        "INSERT INTO produits(nom,prix_vente,description) VALUES(?,?,?)",
        produits
    )
    conn.commit()
    ing  = {row["nom"]: row["id"] for row in c.execute("SELECT id,nom FROM ingredients")}
    prod = {row["nom"]: row["id"] for row in c.execute("SELECT id,nom FROM produits")}
    recettes = [
        (prod["Baklawa"],        ing["Amandes"],     1.5),
        (prod["Baklawa"],        ing["Sucre"],       0.8),
        (prod["Baklawa"],        ing["Beurre"],      0.6),
        (prod["Baklawa"],        ing["Farine"],      0.5),
        (prod["Baklawa"],        ing["Eau de fleur"],0.2),
        (prod["Dziziat"],        ing["Pistaches"],   1.8),
        (prod["Dziziat"],        ing["Sucre"],       1.0),
        (prod["Dziziat"],        ing["Beurre"],      0.8),
        (prod["Dziziat"],        ing["Farine"],      0.4),
        (prod["Tcharak"],        ing["Beurre"],      1.2),
        (prod["Tcharak"],        ing["Farine"],      2.0),
        (prod["Tcharak"],        ing["Sucre"],       0.6),
        (prod["Makrout Amande"], ing["Amandes"],     2.0),
        (prod["Makrout Amande"], ing["Semoule"],     1.5),
        (prod["Makrout Amande"], ing["Miel"],        1.0),
        (prod["Makrout Amande"], ing["Beurre"],      0.5),
        (prod["Griwech"],        ing["Farine"],      2.5),
        (prod["Griwech"],        ing["Miel"],        0.8),
        (prod["Griwech"],        ing["Sucre"],       0.5),
        (prod["Griwech"],        ing["Beurre"],      0.3),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO recettes(produit_id,ingredient_id,quantite_100) VALUES(?,?,?)",
        recettes
    )
    conn.commit()


# ══════════════════════════════════════════════════════
#  INGREDIENTS
# ══════════════════════════════════════════════════════

def get_ingredients():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM ingredients ORDER BY nom").fetchall()

def add_ingredient(nom, unite, stock, stock_min, prix):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO ingredients(nom,unite,stock_actuel,stock_min,prix_unitaire) VALUES(?,?,?,?,?)",
            (nom, unite, stock, stock_min, prix)
        )

def update_ingredient(id, nom, unite, stock, stock_min, prix):
    with get_connection() as conn:
        conn.execute(
            "UPDATE ingredients SET nom=?,unite=?,stock_actuel=?,stock_min=?,prix_unitaire=? WHERE id=?",
            (nom, unite, stock, stock_min, prix, id)
        )

def delete_ingredient(id):
    with get_connection() as conn:
        conn.execute("DELETE FROM ingredients WHERE id=?", (id,))

def get_stock_alerts():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM ingredients WHERE stock_actuel <= stock_min ORDER BY nom"
        ).fetchall()


# ══════════════════════════════════════════════════════
#  ACHATS
# ══════════════════════════════════════════════════════

def add_achat(ingredient_id, quantite, prix_total, fournisseur=""):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO achats(ingredient_id,quantite,prix_total,fournisseur) VALUES(?,?,?,?)",
            (ingredient_id, quantite, prix_total, fournisseur)
        )
        conn.execute(
            "UPDATE ingredients SET stock_actuel = stock_actuel + ? WHERE id=?",
            (quantite, ingredient_id)
        )

def get_achats_history(date_debut=None, date_fin=None):
    """Historique achats avec filtre de dates optionnel."""
    with get_connection() as conn:
        query = """
            SELECT a.*, i.nom as ingredient_nom, i.unite
            FROM achats a JOIN ingredients i ON i.id = a.ingredient_id
        """
        params = []
        conditions = []
        if date_debut:
            conditions.append("DATE(a.created_at) >= ?")
            params.append(date_debut)
        if date_fin:
            conditions.append("DATE(a.created_at) <= ?")
            params.append(date_fin)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY a.created_at DESC LIMIT 100"
        return conn.execute(query, params).fetchall()


# ══════════════════════════════════════════════════════
#  RECETTES
# ══════════════════════════════════════════════════════

def get_recette(produit_id):
    with get_connection() as conn:
        return conn.execute("""
            SELECT r.*, i.nom as ingredient_nom, i.unite
            FROM recettes r JOIN ingredients i ON i.id = r.ingredient_id
            WHERE r.produit_id = ?
        """, (produit_id,)).fetchall()

def set_recette_ligne(produit_id, ingredient_id, quantite_100):
    with get_connection() as conn:
        if quantite_100 > 0:
            conn.execute("""
                INSERT INTO recettes(produit_id,ingredient_id,quantite_100)
                VALUES(?,?,?)
                ON CONFLICT(produit_id,ingredient_id) DO UPDATE SET quantite_100=excluded.quantite_100
            """, (produit_id, ingredient_id, quantite_100))
        else:
            conn.execute(
                "DELETE FROM recettes WHERE produit_id=? AND ingredient_id=?",
                (produit_id, ingredient_id)
            )


# ══════════════════════════════════════════════════════
#  PRODUITS
# ══════════════════════════════════════════════════════

def get_produits():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM produits ORDER BY nom").fetchall()

def add_produit(nom, prix, description=""):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO produits(nom,prix_vente,description) VALUES(?,?,?)",
            (nom, prix, description)
        )

def update_produit(id, nom, prix, description):
    with get_connection() as conn:
        conn.execute(
            "UPDATE produits SET nom=?,prix_vente=?,description=? WHERE id=?",
            (nom, prix, description, id)
        )

def delete_produit(id):
    with get_connection() as conn:
        conn.execute("DELETE FROM produits WHERE id=?", (id,))


# ══════════════════════════════════════════════════════
#  BESOINS STOCK
# ══════════════════════════════════════════════════════

def get_besoin_stock_pour_commande(commande_id):
    with get_connection() as conn:
        lignes = conn.execute(
            "SELECT produit_id, nb_pieces FROM commande_lignes WHERE commande_id=?",
            (commande_id,)
        ).fetchall()
        besoins = {}
        for ligne in lignes:
            recette = conn.execute("""
                SELECT r.ingredient_id, r.quantite_100,
                       i.nom, i.unite, i.stock_actuel
                FROM recettes r
                JOIN ingredients i ON i.id = r.ingredient_id
                WHERE r.produit_id = ?
            """, (ligne["produit_id"],)).fetchall()
            for r in recette:
                iid = r["ingredient_id"]
                besoin = (r["quantite_100"] / 100.0) * ligne["nb_pieces"]
                if iid not in besoins:
                    besoins[iid] = {
                        "nom": r["nom"], "unite": r["unite"],
                        "stock_actuel": r["stock_actuel"], "besoin": 0.0
                    }
                besoins[iid]["besoin"] += besoin
        result = []
        for iid, d in besoins.items():
            manque = max(0.0, d["besoin"] - d["stock_actuel"])
            result.append({
                "ingredient_id": iid,
                "nom":           d["nom"],
                "unite":         d["unite"],
                "besoin":        round(d["besoin"], 3),
                "stock_actuel":  d["stock_actuel"],
                "manque":        round(manque, 3),
                "ok":            manque == 0,
            })
        return sorted(result, key=lambda x: x["nom"])


# ══════════════════════════════════════════════════════
#  DEDUCTION STOCK
# ══════════════════════════════════════════════════════

def _modifier_stock_commande(conn, commande_id, facteur):
    lignes = conn.execute(
        "SELECT produit_id, nb_pieces FROM commande_lignes WHERE commande_id=?",
        (commande_id,)
    ).fetchall()
    for ligne in lignes:
        recette = conn.execute(
            "SELECT ingredient_id, quantite_100 FROM recettes WHERE produit_id=?",
            (ligne["produit_id"],)
        ).fetchall()
        for r in recette:
            delta = facteur * (r["quantite_100"] / 100.0) * ligne["nb_pieces"]
            conn.execute(
                "UPDATE ingredients SET stock_actuel = stock_actuel + ? WHERE id=?",
                (delta, r["ingredient_id"])
            )


# ══════════════════════════════════════════════════════
#  COMMANDES
# ══════════════════════════════════════════════════════

def get_commandes(statut=None, date_debut=None, date_fin=None):
    """Retourne les commandes avec filtres optionnels statut + dates."""
    with get_connection() as conn:
        conditions = []
        params = []
        if statut:
            conditions.append("statut=?")
            params.append(statut)
        if date_debut:
            conditions.append("DATE(created_at) >= ?")
            params.append(date_debut)
        if date_fin:
            conditions.append("DATE(created_at) <= ?")
            params.append(date_fin)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        query = f"SELECT * FROM commandes {where} ORDER BY created_at DESC"
        return conn.execute(query, params).fetchall()

def get_commande_detail(commande_id):
    with get_connection() as conn:
        commande = conn.execute(
            "SELECT * FROM commandes WHERE id=?", (commande_id,)
        ).fetchone()
        lignes = conn.execute("""
            SELECT cl.*, p.nom as produit_nom
            FROM commande_lignes cl
            JOIN produits p ON p.id = cl.produit_id
            WHERE cl.commande_id = ?
        """, (commande_id,)).fetchall()
        return commande, lignes

def add_commande(client, telephone, date_livraison, notes, lignes):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO commandes(client,telephone,date_livraison,notes) VALUES(?,?,?,?)",
            (client, telephone, date_livraison, notes)
        )
        commande_id = cur.lastrowid
        for produit_id, nb, prix in lignes:
            conn.execute(
                "INSERT INTO commande_lignes(commande_id,produit_id,nb_pieces,prix_unitaire) VALUES(?,?,?,?)",
                (commande_id, produit_id, nb, prix)
            )
        return commande_id

def update_statut_commande(commande_id, nouveau_statut):
    with get_connection() as conn:
        cmd = conn.execute(
            "SELECT statut, stock_deduit FROM commandes WHERE id=?", (commande_id,)
        ).fetchone()
        if not cmd:
            return
        if nouveau_statut == "livree" and not cmd["stock_deduit"]:
            _modifier_stock_commande(conn, commande_id, -1)
            conn.execute(
                "UPDATE commandes SET statut=?, stock_deduit=1 WHERE id=?",
                (nouveau_statut, commande_id)
            )
        elif cmd["statut"] == "livree" and nouveau_statut != "livree" and cmd["stock_deduit"]:
            _modifier_stock_commande(conn, commande_id, +1)
            conn.execute(
                "UPDATE commandes SET statut=?, stock_deduit=0 WHERE id=?",
                (nouveau_statut, commande_id)
            )
        else:
            conn.execute(
                "UPDATE commandes SET statut=? WHERE id=?",
                (nouveau_statut, commande_id)
            )

def delete_commande(commande_id):
    with get_connection() as conn:
        cmd = conn.execute(
            "SELECT stock_deduit FROM commandes WHERE id=?", (commande_id,)
        ).fetchone()
        if cmd and cmd["stock_deduit"]:
            _modifier_stock_commande(conn, commande_id, +1)
        conn.execute("DELETE FROM commandes WHERE id=?", (commande_id,))

def get_total_commande(commande_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(nb_pieces * prix_unitaire), 0) as total FROM commande_lignes WHERE commande_id=?",
            (commande_id,)
        ).fetchone()
        return row["total"] or 0


# ══════════════════════════════════════════════════════
#  STATISTIQUES avec filtre de dates
# ══════════════════════════════════════════════════════

def get_stats(date_debut=None, date_fin=None):
    """Stats globales ou filtrées par plage de dates."""
    with get_connection() as conn:
        # Filtres de date pour commandes
        date_cond = ""
        date_params = []
        if date_debut:
            date_cond += " AND DATE(c.created_at) >= ?"
            date_params.append(date_debut)
        if date_fin:
            date_cond += " AND DATE(c.created_at) <= ?"
            date_params.append(date_fin)

        date_cond_simple = ""
        date_params_simple = []
        if date_debut:
            date_cond_simple += " AND DATE(created_at) >= ?"
            date_params_simple.append(date_debut)
        if date_fin:
            date_cond_simple += " AND DATE(created_at) <= ?"
            date_params_simple.append(date_fin)

        nb_attente = conn.execute(
            f"SELECT COUNT(*) FROM commandes WHERE statut='en_attente'{date_cond_simple}",
            date_params_simple
        ).fetchone()[0]

        nb_total = conn.execute(
            f"SELECT COUNT(*) FROM commandes WHERE 1=1{date_cond_simple}",
            date_params_simple
        ).fetchone()[0]

        ca_total = conn.execute(f"""
            SELECT COALESCE(SUM(cl.nb_pieces * cl.prix_unitaire), 0)
            FROM commande_lignes cl
            JOIN commandes c ON c.id = cl.commande_id
            WHERE c.statut = 'livree'{date_cond}
        """, date_params).fetchone()[0]

        valeur_stock = conn.execute(
            "SELECT COALESCE(SUM(stock_actuel * prix_unitaire), 0) FROM ingredients"
        ).fetchone()[0]

        nb_alertes = conn.execute(
            "SELECT COUNT(*) FROM ingredients WHERE stock_actuel <= stock_min"
        ).fetchone()[0]

        ca_mois = conn.execute(f"""
            SELECT strftime('%Y-%m', c.created_at) as mois,
                   SUM(cl.nb_pieces * cl.prix_unitaire) as total
            FROM commande_lignes cl
            JOIN commandes c ON c.id = cl.commande_id
            WHERE c.statut = 'livree'{date_cond}
            GROUP BY mois ORDER BY mois DESC LIMIT 6
        """, date_params).fetchall()

        # Nombre de commandes livrées dans la période
        nb_livrees = conn.execute(
            f"SELECT COUNT(*) FROM commandes WHERE statut='livree'{date_cond_simple}",
            date_params_simple
        ).fetchone()[0]

        # Dépenses achats dans la période
        achat_cond = ""
        achat_params = []
        if date_debut:
            achat_cond += " AND DATE(created_at) >= ?"
            achat_params.append(date_debut)
        if date_fin:
            achat_cond += " AND DATE(created_at) <= ?"
            achat_params.append(date_fin)
        depenses_achats = conn.execute(
            f"SELECT COALESCE(SUM(prix_total),0) FROM achats WHERE 1=1{achat_cond}",
            achat_params
        ).fetchone()[0]

        return {
            "commandes_attente":  nb_attente,
            "commandes_total":    nb_total,
            "commandes_livrees":  nb_livrees,
            "ca_total":           ca_total,
            "valeur_stock":       valeur_stock,
            "nb_alertes":         nb_alertes,
            "ca_mois":            ca_mois,
            "depenses_achats":    depenses_achats,
        }


def get_date_range_for_period(period):
    """
    Retourne (date_debut, date_fin) en format 'YYYY-MM-DD' pour une periode donnee.
    period: 'today', 'week', 'month', 'month3', 'year', ou None (tout)
    """
    today = datetime.now().date()
    if period == "today":
        return str(today), str(today)
    elif period == "week":
        debut = today - timedelta(days=today.weekday())  # lundi
        return str(debut), str(today)
    elif period == "month":
        debut = today.replace(day=1)
        return str(debut), str(today)
    elif period == "month3":
        # 3 derniers mois
        mois = today.month - 2
        annee = today.year
        if mois <= 0:
            mois += 12
            annee -= 1
        debut = today.replace(year=annee, month=mois, day=1)
        return str(debut), str(today)
    elif period == "year":
        debut = today.replace(month=1, day=1)
        return str(debut), str(today)
    return None, None  # pas de filtre = tout
