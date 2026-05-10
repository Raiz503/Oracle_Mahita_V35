"""
╔══════════════════════════════════════════════════════════════╗
║           ORACLE MAHITA V37.0 — IA INTÉGRÉE                 ║
║           OCR Bet261 · Apprentissage · Chat IA              ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import easyocr
import re
import json
import os
from difflib import get_close_matches
from PIL import Image, ImageEnhance
import numpy as np
import io
import math
from typing import List, Dict

# ── NOUVEAUX IMPORTS POUR L'OCR ──
from scipy.signal import find_peaks
from scipy.ndimage import uniform_filter1d

# ── Import IA (v53 en priorité, fallback v49) ──
try:
    from moteur_apprentissage_v53 import moteur_apprentissage
    IA_DISPONIBLE = True
except ImportError:
    try:
        from moteur_apprentissage import moteur_apprentissage
        IA_DISPONIBLE = True
    except ImportError:
        IA_DISPONIBLE = False
        moteur_apprentissage = None

try:
    from moteur_ia_chat import moteur_ia_chat
    CHAT_IA_DISPONIBLE = True
except ImportError:
    CHAT_IA_DISPONIBLE = False
    moteur_ia_chat = None

# ── Import Cerveau (fichier externe ou fallback intégré) ──
try:
    from cerveau_1 import cerveau1 as oracle_brain   # ✅ FIX: nom réel du fichier
    CERVEAU_DISPONIBLE = True
except ImportError:
    try:
        from moteur_cerveau1 import cerveau1 as oracle_brain  # fallback ancien nom
        CERVEAU_DISPONIBLE = True
    except ImportError:
        # ══ CERVEAU INLINE FALLBACK ══
        class _CerveauInline:
            """Cerveau analytique intégré — utilisé si moteur_cerveau1.py est absent."""
            def analyser_match(self, equipe_dom, equipe_ext, cotes, journee=1,
                               rang_dom=10, rang_ext=10, serie_dom=0, serie_ext=0,
                               forme_dom=None, forme_ext=None, match_precedent_dom=None):
                c1, cx, c2 = cotes
                # Forces de base (inverse des cotes)
                f1 = 1/c1; fx = 1/cx; f2 = 1/c2
                # Ajustement classement
                diff = (rang_ext - rang_dom) * 0.018
                f1 += diff; f2 -= diff
                # Ajustement forme
                if forme_dom:
                    pts = sum(3 if r=="V" else (1 if r=="N" else 0) for r in forme_dom[-5:])
                    f1 += pts * 0.012
                if forme_ext:
                    pts = sum(3 if r=="V" else (1 if r=="N" else 0) for r in forme_ext[-5:])
                    f2 += pts * 0.012
                # Série victoires
                f1 += serie_dom * 0.025; f2 += serie_ext * 0.025
                tot = f1 + fx + f2
                p1 = f1/tot; px = fx/tot; p2 = f2/tot
                if p1 > px and p1 > p2:
                    pred, conf, cote_c = "1", int(p1*100), c1
                    choix = f"{equipe_dom} (cote {c1})"
                elif p2 > p1 and p2 > px:
                    pred, conf, cote_c = "2", int(p2*100), c2
                    choix = f"{equipe_ext} (cote {c2})"
                else:
                    pred, conf, cote_c = "X", int(px*100), cx
                    choix = f"Nul (cote {cx})"
                if conf >= 72:   label = "BANKER"
                elif conf >= 54: label = "RISQUE CALCULÉ"
                else:            label = "FUN"
                # Score estimé simple
                bd = max(1,round(p1*4)) if pred=="1" else (max(0,round(p1*2)) if pred=="2" else max(1,round(p1*2.5)))
                be = max(0,round(p2*2)) if pred=="1" else (max(1,round(p2*4)) if pred=="2" else bd)
                score_p = f"{min(bd,5)}:{min(be,5)}"
                return {
                    "prediction": pred, "choix_expert": choix,
                    "indice_confiance": conf, "confiance": label,
                    "score_predit": score_p,
                    "proba": {"1": round(p1,3), "X": round(px,3), "2": round(p2,3)}
                }
            def calculer_performance_globale(self, history_saison):
                total = bon = 0
                for jdata in history_saison.values():
                    for r in jdata.get("res", []):
                        try:
                            sh, sa = map(int, r['s'].replace('-',':').split(':'))
                            total += 1
                        except: pass
                return {"total_matchs": total, "taux_1n2": 0, "scores_exacts": 0, "moyenne_points": 0}
        oracle_brain = _CerveauInline()
    CERVEAU_DISPONIBLE = False  # indique que c'est le fallback

# ── Configuration ──
st.set_page_config(page_title="Oracle Mahita V52", layout="wide", page_icon="🔮")

# ── CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');

.main-header {
    padding: 12px 20px;
    background: linear-gradient(135deg, #071410 0%, #0a1f16 100%);
    margin-bottom: 20px;
    border: 1.5px solid #1a4a2a;
    border-radius: 14px;
    box-shadow: 0 0 30px rgba(0,255,136,0.12), inset 0 0 20px rgba(0,255,136,0.03);
}
.prono-safe { border-left: 5px solid #00FF00; padding: 14px; background: rgba(0,255,0,0.08); border-radius: 8px; margin: 10px 0; }
.prono-risque { border-left: 5px solid #FFA500; padding: 14px; background: rgba(255,165,0,0.08); border-radius: 8px; margin: 10px 0; }
.prono-fun { border-left: 5px solid #FF4B4B; padding: 14px; background: rgba(255,75,75,0.08); border-radius: 8px; margin: 10px 0; }
.next-day-box { text-align: center; color: #7FFFD4; font-weight: bold; font-size: 1.3em; padding: 12px;
                background: rgba(127,255,212,0.12); border-radius: 10px; margin: 15px 0; }
.chat-user { background: rgba(127,255,212,0.1); border-left: 3px solid #7FFFD4; 
             padding: 10px 15px; margin: 5px 0 5px 40px; border-radius: 10px; }
.chat-bot { background: rgba(255,255,255,0.05); border-left: 3px solid #00FF00; 
            padding: 10px 15px; margin: 5px 40px 5px 0; border-radius: 10px; }
.chat-bot-offline { background: rgba(255,255,255,0.05); border-left: 3px solid #FFA500; 
                    padding: 10px 15px; margin: 5px 40px 5px 0; border-radius: 10px; }

</style>
""", unsafe_allow_html=True)

# ===================== LOGO PNG (Base64) =====================
LOGO_PNG_B64 = "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"
# ===================== UTILITAIRES =====================
def custom_notify(text: str, color: str = "#00FF00"):
    st.markdown(f"""
    <div style="padding:18px;border:3px solid {color};border-radius:12px;background:#0E1117;color:#FFF;
    text-align:center;font-weight:900;box-shadow:0 0 25px {color};margin:15px 0;font-size:1.25em;">
    {text}</div>""", unsafe_allow_html=True)

def get_standings(season_data: dict, teams_list: list) -> pd.DataFrame:
    stats = {t: {"MJ":0,"V":0,"N":0,"D":0,"BP":0,"BC":0,"Diff":0,"Pts":0} for t in teams_list}
    for data in season_data.values():
        for m in data.get("res", []):
            try:
                sh, sa = map(int, m['s'].replace('-',':').split(':'))
                h, a = m['h'], m['a']
                stats[h]["MJ"] += 1; stats[a]["MJ"] += 1
                stats[h]["BP"] += sh; stats[h]["BC"] += sa
                stats[a]["BP"] += sa; stats[a]["BC"] += sh
                if sh > sa:
                    stats[h]["V"] += 1; stats[h]["Pts"] += 3; stats[a]["D"] += 1
                elif sh < sa:
                    stats[a]["V"] += 1; stats[a]["Pts"] += 3; stats[h]["D"] += 1
                else:
                    stats[h]["N"] += 1; stats[h]["Pts"] += 1
                    stats[a]["N"] += 1; stats[a]["Pts"] += 1
            except: continue
    df = pd.DataFrame.from_dict(stats, orient='index').reset_index().rename(columns={'index': 'Équipe'})
    df['Diff'] = df['BP'] - df['BC']
    df = df.sort_values(by=["Pts","Diff","BP"], ascending=False).reset_index(drop=True)
    df.insert(0, 'Rang', range(1, len(df)+1))
    return df

def get_forme_equipe(history: dict, saison: str, equipe: str, nb_matchs: int = 6) -> List[str]:
    resultats = []
    if saison not in history: return []
    journees = sorted(history[saison].keys(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
    for jk in reversed(journees):
        if len(resultats) >= nb_matchs: break
        for match in history[saison][jk].get("res", []):
            try:
                sh, sa = map(int, match["s"].replace("-", ":").split(":"))
                if match["h"] == equipe:
                    resultats.insert(0, "V" if sh > sa else ("N" if sh == sa else "D"))
                elif match["a"] == equipe:
                    resultats.insert(0, "V" if sa > sh else ("N" if sh == sa else "D"))
            except: continue
    return resultats[-nb_matchs:]

def get_serie_victoires(forme: List[str]) -> int:
    serie = 0
    for r in reversed(forme):
        if r == "V": serie += 1
        else: break
    return serie

def get_dernier_adversaire(history: dict, saison: str, equipe: str):
    if saison not in history: return None
    journees = sorted(history[saison].keys(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
    for jk in reversed(journees):
        for match in history[saison][jk].get("res", []):
            if match.get("h") == equipe: return match.get("a")
            if match.get("a") == equipe: return match.get("h")
    return None

# ===================== PERSISTENCE =====================
DB_FILE = "oracle_history.json"
CHAT_FILE = "oracle_chat_history.json"
CHAT_SESSIONS_FILE = "oracle_chat_sessions.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"Erreur de sauvegarde : {e}")

def load_chat_history():
    if os.path.exists(CHAT_FILE):
        try:
            with open(CHAT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def save_chat_history(messages):
    try:
        with open(CHAT_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
    except Exception as e:
        pass

# ── Multi-session chat ──
def load_chat_sessions() -> dict:
    """Charge toutes les sessions de chat. Format: {session_id: {title, created, messages}}"""
    if os.path.exists(CHAT_SESSIONS_FILE):
        try:
            with open(CHAT_SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_chat_sessions(sessions: dict):
    try:
        with open(CHAT_SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
    except: pass

def new_chat_session(title: str = "") -> str:
    """Crée une nouvelle session et retourne son ID."""
    import datetime as _dtm
    sid = _dtm.datetime.now().strftime("%Y%m%d_%H%M%S")
    sessions = load_chat_sessions()
    sessions[sid] = {
        "title": title or f"Chat {_dtm.datetime.now().strftime('%d/%m %H:%M')}",
        "created": _dtm.datetime.now().isoformat(),
        "messages": []
    }
    save_chat_sessions(sessions)
    return sid

def get_or_create_active_session() -> str:
    """Retourne l'ID de session active, en crée une si nécessaire."""
    sessions = load_chat_sessions()
    if st.session_state.get('active_chat_session') and st.session_state['active_chat_session'] in sessions:
        return st.session_state['active_chat_session']
    if sessions:
        sid = sorted(sessions.keys())[-1]
        st.session_state['active_chat_session'] = sid
        return sid
    sid = new_chat_session()
    st.session_state['active_chat_session'] = sid
    return sid

def save_session_messages(sid: str, messages: list):
    sessions = load_chat_sessions()
    if sid in sessions:
        sessions[sid]["messages"] = messages
        # Auto-titre basé sur le 1er message utilisateur
        if not sessions[sid].get("_titled") and messages:
            first_user = next((m["content"] for m in messages if m.get("role") == "user"), None)
            if first_user:
                sessions[sid]["title"] = first_user[:40] + ("…" if len(first_user) > 40 else "")
                sessions[sid]["_titled"] = True
        save_chat_sessions(sessions)

def load_session_messages(sid: str) -> list:
    sessions = load_chat_sessions()
    return sessions.get(sid, {}).get("messages", [])

def build_full_context(history: dict, saison_active: str, standings: pd.DataFrame, next_j: int) -> str:
    """Construit un contexte complet avec TOUTES les données de l'historique pour l'IA."""
    ctx = []
    ctx.append(f"=== ORACLE MAHITA — DONNÉES COMPLÈTES ===")
    ctx.append(f"Saison active : {saison_active}")
    ctx.append(f"Prochaine journée : J-{next_j}")
    ctx.append("")

    # Classement
    ctx.append("--- CLASSEMENT ACTUEL ---")
    if not standings.empty:
        for _, row in standings.iterrows():
            ctx.append(f"  {int(row['Rang'])}. {row['Équipe']} | {int(row['MJ'])} MJ | {int(row['V'])}V {int(row['N'])}N {int(row['D'])}D | BP:{int(row['BP'])} BC:{int(row['BC'])} Diff:{int(row['Diff'])} | {int(row['Pts'])} pts")
    ctx.append("")

    # Toutes les journées de toutes les saisons
    for saison, saison_data in history.items():
        ctx.append(f"=== SAISON : {saison} ===")
        journees = sorted(saison_data.keys(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
        for jk in journees:
            jdata = saison_data[jk]
            ctx.append(f"\n-- {jk} --")

            # Calendrier
            cal = jdata.get("cal", [])
            if cal:
                ctx.append("  CALENDRIER & COTES:")
                for m in cal:
                    cotes = m.get('o', ['-', '-', '-'])
                    c_str = f"1={cotes[0]} X={cotes[1] if len(cotes)>1 else '-'} 2={cotes[2] if len(cotes)>2 else '-'}"
                    ctx.append(f"    {m.get('h','?')} vs {m.get('a','?')} | {c_str}")

            # Pronos
            pro = jdata.get("pro", [])
            if pro:
                ctx.append("  PRONOSTICS:")
                for p in pro:
                    ctx.append(f"    {p.get('h','?')} vs {p.get('a','?')} → Prono:{p.get('p','?')} Conf:{p.get('c','?')}%")

            # Résultats
            res = jdata.get("res", [])
            if res:
                ctx.append("  RÉSULTATS:")
                for r in res:
                    score = r.get('s', '?')
                    mt = r.get('mt', '')
                    hm = r.get('hm', '')
                    am = r.get('am', '')
                    line = f"    {r.get('h','?')} {score} {r.get('a','?')}"
                    if mt: line += f" (MT:{mt})"
                    if hm: line += f" | Buteurs dom: {hm}"
                    if am: line += f" | Buteurs ext: {am}"
                    ctx.append(line)
        ctx.append("")

    return "\n".join(ctx)

if 'history' not in st.session_state:
    st.session_state['history'] = load_db()
    if not st.session_state['history']:
        st.session_state['history']["Saison 2026"] = {}

# ── Charger l'historique chat persistant ──
if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = load_chat_history()

# ── Initialiser IA Apprentissage — UNIQUEMENT si les patterns sont vides ──
# CORRECTION BUG: ce bloc ne doit s'exécuter qu'UNE SEULE FOIS (1ère utilisation).
# Le flag session_state se réinitialise à chaque rechargement de page, ce qui
# provoquait un réapprentissage de TOUS les matchs à chaque session → compteurs x30.
# Solution: vérifier d'abord si le moteur a déjà des patterns sauvegardés.
if IA_DISPONIBLE and not st.session_state.get('_ia_history_loaded'):
    try:
        _stats_existants = moteur_apprentissage.get_stats_apprentissage()
        _patterns_vides = _stats_existants.get('total', 0) == 0
        if _patterns_vides:
            # 1ère utilisation seulement : charger tout l'historique
            for saison, saison_data in st.session_state['history'].items():
                journees = sorted(saison_data.keys(),
                                  key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
                for jk in journees:
                    jdata = saison_data[jk]
                    cal_ia = jdata.get("cal", [])
                    res_ia = jdata.get("res", [])
                    for i, m in enumerate(res_ia):
                        try:
                            sh, sa = map(int, m['s'].replace('-', ':').split(':'))
                            resultat = "1" if sh > sa else ("X" if sh == sa else "2")
                            cotes = cal_ia[i].get('o', [2.0, 3.0, 3.0]) if cal_ia and i < len(cal_ia) else [2.0, 3.0, 3.0]
                            moteur_apprentissage.analyser_pattern_cotes(cotes[0], cotes[1], cotes[2], resultat)
                            moteur_apprentissage.analyser_pattern_equipe(
                                m['h'],
                                "V" if resultat == "1" else ("N" if resultat == "X" else "D"),
                                {"domicile": True}
                            )
                            moteur_apprentissage.analyser_pattern_equipe(
                                m['a'],
                                "V" if resultat == "2" else ("N" if resultat == "X" else "D"),
                                {"domicile": False}
                            )
                        except:
                            pass
            moteur_apprentissage.save()
        # Sinon: patterns déjà chargés depuis le fichier sauvegardé → on ne recharge pas
    except:
        pass
    finally:
        st.session_state['_ia_history_loaded'] = True

# ===================== OCR ENGINE =====================
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en', 'fr'], gpu=False)

reader = load_ocr()

class OracleEngine:
    def __init__(self):
        self.teams_list = [
            "Leeds", "Brighton", "A. Villa", "Manchester Blue", "C. Palace",
            "Bournemouth", "Spurs", "Burnley", "West Ham", "Liverpool",
            "Fulham", "Newcastle", "Manchester Red", "Everton", "London Blues",
            "Wolverhampton", "Sunderland", "N. Forest", "London Reds", "Brentford"
        ]

    def clean_team(self, text: str):
        if not text: return None
        m = get_close_matches(text.strip(), self.teams_list, n=1, cutoff=0.35)
        return m[0] if m else None

engine = OracleEngine()

# ===================== OCR CALENDRIER (CORRIGÉ) =====================
def ocr_calendrier_bet261(image_bytes, debug=False):
    """OCR avancé pour calendrier Bet261 avec détection boutons verts et correction cotes.
    VERSION CORRIGÉE - Détecte correctement les deux équipes par match."""
    img = Image.open(io.BytesIO(image_bytes))
    img_array = np.array(img)
    h_img, w_img = img_array.shape[:2]

    import cv2
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)

    # Masque vert Bet261
    lower_green = np.array([20, 30, 80])
    upper_green = np.array([100, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)

    # Fermer les contours
    kernel = np.ones((5,5), np.uint8)
    green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)

    # Trouver les contours des boutons
    contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boutons = []
    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        area = bw * bh
        aspect = bw / bh if bh > 0 else 0
        if 500 < area < 15000 and 1.0 < aspect < 8.0 and bw > 30 and bh > 10:
            boutons.append({
                'x': x, 'y': y, 'w': bw, 'h': bh,
                'cx': x + bw//2, 'cy': y + bh//2,
                'area': area
            })

    # === CORRECTION 1: Filtrer le bouton panier (coin bas droit, très grand) ===
    boutons = [b for b in boutons if not (b['x'] > w_img * 0.75 and b['y'] > h_img * 0.80 and b['area'] > 5000)]

    # Trier et grouper par lignes
    boutons.sort(key=lambda b: (b['cy'], b['cx']))
    lignes = []
    for b in boutons:
        placed = False
        for ligne in lignes:
            if abs(b['cy'] - ligne['cy_mean']) < 40:
                ligne['boutons'].append(b)
                ligne['cy_mean'] = sum(x['cy'] for x in ligne['boutons']) / len(ligne['boutons'])
                placed = True
                break
        if not placed:
            lignes.append({'cy_mean': b['cy'], 'boutons': [b]})

    # Filtrer lignes avec >= 2 boutons
    lignes_valides = [l for l in lignes if len(l['boutons']) >= 2]

    # Ignorer header
    min_y = int(h_img * 0.05)
    lignes_valides = [l for l in lignes_valides if l['cy_mean'] > min_y]

    # Pour les lignes avec 2 boutons, ajouter un 3ème bouton "fantôme"
    for ligne in lignes_valides:
        if len(ligne['boutons']) == 2:
            b1, b2 = sorted(ligne['boutons'], key=lambda b: b['cx'])
            espacement = b2['cx'] - b1['cx']
            b3_x = b2['cx'] + espacement
            b3_y = b2['cy']
            ligne['boutons'].append({
                'x': int(b3_x - b2['w']//2),
                'y': b2['y'],
                'w': b2['w'],
                'h': b2['h'],
                'cx': int(b3_x),
                'cy': b3_y,
                'fantome': True
            })

    # Limiter à 10
    lignes_valides = sorted(lignes_valides, key=lambda x: x['cy_mean'])[:10]

    if len(lignes_valides) == 0:
        return []

    matchs = []

    for i, ligne in enumerate(lignes_valides):
        y_center = int(ligne['cy_mean'])
        
        # === CORRECTION V2: Zone plus grande pour capturer les deux noms ===
        y_start = max(0, y_center - 80)
        y_end = min(h_img, y_center + 80)
        
        # Zone noms: toute la largeur
        ligne_full = img.crop((0, y_start, w_img, y_end))

        # Extraire cotes
        cotes_detectees = [None, None, None]
        boutons_sorted = sorted(ligne['boutons'], key=lambda b: b['cx'])

        for idx, btn in enumerate(boutons_sorted[:3]):
            marge = 3
            left = max(0, btn['x'] + marge)
            top = max(0, btn['y'] + marge)
            right = min(w_img, btn['x'] + btn['w'] - marge)
            bottom = min(h_img, btn['y'] + btn['h'] - marge)

            zone_cote = img.crop((left, top, right, bottom))

            try:
                cote_array = np.array(zone_cote)
                res = reader.readtext(cote_array, detail=0, paragraph=False)
                if res:
                    texte = ' '.join(res).strip()
                    texte = texte.replace(',', '.').replace(' ', '')
                    texte = texte.replace('O', '0').replace('o', '0').replace('l', '1')
                    texte = texte.replace('I', '1').replace('S', '5').replace('s', '5')

                    match_nb = re.search(r'(\d+\.?\d*)', texte)
                    if match_nb:
                        val = float(match_nb.group(1))

                        if val > 20.0:
                            corrections = []
                            for div in [10, 100]:
                                corr = val / div
                                if 1.0 <= corr <= 20.0:
                                    corrections.append(corr)

                            texte_original = ' '.join(res).strip()
                            if ',' in texte_original or '.' in texte_original:
                                match_corr = re.search(r'(\d+)[,\.](\d+)', texte_original)
                                if match_corr:
                                    partie_entiere = int(match_corr.group(1))
                                    partie_decimale = int(match_corr.group(2))
                                    if partie_entiere < 10 and len(str(partie_decimale)) == 2:
                                        corr = float(f"{partie_entiere}.{partie_decimale}")
                                        if 1.0 <= corr <= 20.0:
                                            corrections.append(corr)

                            if corrections:
                                val = min(corrections)
                            else:
                                val = None

                        if val is not None and 1.0 <= val <= 20.0:
                            cotes_detectees[idx] = val
            except:
                pass

        # === CORRECTION V2: Détection des noms avec zone spécifique gauche ===
        noms_detectes = []
        try:
            # Zone GAUCHE où sont les noms (pas les cotes)
            zone_noms = img.crop((0, y_start, int(w_img * 0.45), y_end))
            zone_noms_array = np.array(zone_noms)
            
            # Améliorer le contraste
            zone_noms_pil = Image.fromarray(zone_noms_array)
            enhancer = ImageEnhance.Contrast(zone_noms_pil)
            zone_noms_contraste = np.array(enhancer.enhance(2.5))
            
            # OCR avec détail complet
            res_noms = reader.readtext(zone_noms_contraste, detail=1, paragraph=False)
            
            if debug:
                print(f"\n--- Match {i+1} ---")
                print(f"Zone noms trouvés: {len(res_noms)}")
            
            # Filtrer et regrouper par position Y
            texts_avec_y = []
            for bbox, text, prob in res_noms:
                if prob > 0.20 and len(text) > 1:  # Seuil baissé à 0.20
                    cy = (bbox[0][1] + bbox[2][1]) / 2
                    texts_avec_y.append((cy, text, prob))
                    if debug:
                        print(f"  Texte: '{text}' | Y: {cy:.1f} | Prob: {prob:.2f}")
            
            # Trier par position Y (du haut vers le bas)
            texts_avec_y.sort(key=lambda x: x[0])
            
            # Prendre les 2 premiers noms distincts
            noms_bruts = []
            for cy, text, prob in texts_avec_y:
                # Éviter les doublons très proches en Y
                if not noms_bruts or abs(cy - noms_bruts[-1][0]) > 15:
                    noms_bruts.append((cy, text, prob))
                if len(noms_bruts) >= 2:
                    break
            
            noms_detectes = noms_bruts

        except Exception as e:
            if debug:
                print(f"Erreur OCR noms match {i+1}: {e}")
            pass

        # === Assigner équipes ===
        dom_default = ""
        ext_default = ""

        if len(noms_detectes) >= 2:
            # Premier nom = domicile (plus haut), Deuxième = extérieur (plus bas)
            nom_dom_ocr = noms_detectes[0][1]
            nom_ext_ocr = noms_detectes[1][1]
            
            if debug:
                print(f"  DOM OCR: '{nom_dom_ocr}' | EXT OCR: '{nom_ext_ocr}'")

            dom_match = get_close_matches(nom_dom_ocr, engine.teams_list, n=1, cutoff=0.35)
            if dom_match:
                dom_default = dom_match[0]

            ext_match = get_close_matches(nom_ext_ocr, engine.teams_list, n=1, cutoff=0.35)
            if ext_match:
                ext_default = ext_match[0]
                
        elif len(noms_detectes) == 1:
            nom_brut = noms_detectes[0][1]
            match = get_close_matches(nom_brut, engine.teams_list, n=1, cutoff=0.35)
            if match:
                dom_default = match[0]

        if debug:
            print(f"  RESULTAT: DOM='{dom_default}' | EXT='{ext_default}'")

        matchs.append({
            'index': i,
            'h': dom_default,
            'a': ext_default,
            'o': cotes_detectees,
            'ligne_img': img.crop((0, y_start, w_img, y_end))
        })

    return matchs

# ===================== OCR RÉSULTATS (CORRIGÉ V10 - NOMS + MT + BUTEURS) =====================
def ocr_resultats_bet261(image_bytes, debug=False):
    """OCR avancé pour résultats Bet261 - VERSION V10.
    Corrections: noms d'équipes, MT, et isolation des buteurs."""
    img = Image.open(io.BytesIO(image_bytes))
    img_array = np.array(img)
    h_img, w_img = img_array.shape[:2]

    import cv2

    # === DÉTECTION: HSV + masque gris ===
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
    gray_mask = (hsv[:,:,1] < 50) & (hsv[:,:,2] > 40) & (hsv[:,:,2] < 180)
    gray_mask = gray_mask.astype(np.uint8)

    kernel = np.ones((5,5), np.uint8)
    gray_mask = cv2.morphologyEx(gray_mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(gray_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rectangles = []
    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        area = bw * bh
        aspect = bw / bh if bh > 0 else 0
        if 1000 < area < 8000 and 0.8 < aspect < 2.5 and bw > 40 and bh > 25:
            rectangles.append({'x': x, 'y': y, 'w': bw, 'h': bh, 'cx': x+bw//2, 'cy': y+bh//2})

    rectangles.sort(key=lambda r: r['cy'])
    min_y = int(h_img * 0.15)
    rectangles = [r for r in rectangles if r['cy'] > min_y]
    rectangles = rectangles[:10]

    if len(rectangles) == 0:
        return []

    matches = []

    for i, rect in enumerate(rectangles):
        y_center = rect['cy']
        rect_top = rect['y']
        rect_bot = rect['y'] + rect['h']

        # === STRUCTURE RÉELLE BET261 RÉSULTATS ===
        # Le rectangle gris contient le SCORE FINAL (ex: "1:0")
        # Les NOMS d'équipes sont au niveau du rectangle, côté gauche et droite
        # Sous le rectangle: buteurs gauche + "MT: X:X" + buteurs droite

        # Zone complète de la ligne pour affichage
        y_start = max(0, rect_top - 15)
        y_end = min(h_img, rect_bot + 50)
        ligne_img = img.crop((0, y_start, w_img, y_end))

        # === ZONE CENTRE: score UNIQUEMENT (intérieur du rectangle gris) ===
        zone_centre = img.crop((rect['x'] - 5, rect_top, rect['x'] + rect['w'] + 5, rect_bot))

        # === ZONES NOMS: au niveau exact du rectangle, côtés gauche et droite ===
        # Légèrement plus large que le rect pour capturer le texte centré verticalement
        y_nom_start = max(0, rect_top - 5)
        y_nom_end = min(h_img, rect_bot + 5)
        zone_nom_gauche = img.crop((0, y_nom_start, rect['x'] - 10, y_nom_end))
        zone_nom_droite = img.crop((rect['x'] + rect['w'] + 10, y_nom_start, w_img, y_nom_end))

        # === ZONES SOUS LE RECT: buteurs + MT ===
        # MT et buteurs sont sur la même bande sous le rectangle
        y_sub_start = rect_bot
        y_sub_end = min(h_img, rect_bot + 38)
        # Buteurs dom: côté gauche (sous le nom dom) — légèrement élargi
        zone_but_gauche = img.crop((0, y_sub_start, rect['x'] - 5, y_sub_end))
        # Buteurs ext: côté droit (sous le nom ext) — légèrement élargi
        zone_but_droite = img.crop((rect['x'] + rect['w'] + 5, y_sub_start, w_img, y_sub_end))
        # MT: zone centrale sous le rect
        zone_mt = img.crop((rect['x'] - 20, y_sub_start, rect['x'] + rect['w'] + 20, y_sub_end))

        equipe_dom = ""
        equipe_ext = ""
        score = ""
        mt = ""
        buteurs_dom = ""
        buteurs_ext = ""

        # === SCORE FINAL (zone centre = intérieur du rectangle gris) ===
        try:
            centre_array = np.array(zone_centre)
            centre_pil = Image.fromarray(centre_array)
            enhancer = ImageEnhance.Contrast(centre_pil)
            centre_contraste = np.array(enhancer.enhance(3.0))

            res_centre = reader.readtext(centre_contraste, detail=1, paragraph=False)

            if debug:
                print(f"\n--- Match {i+1} CENTRE (score) ---")
                for bbox, text, prob in res_centre:
                    cy = (bbox[0][1] + bbox[2][1]) / 2
                    print(f"  Y={cy:.1f}: '{text}' | prob: {prob:.2f}")

            # Chercher le score parmi tous les textes détectés
            for bbox, text, prob in sorted(res_centre, key=lambda x: (x[0][0][1]+x[0][2][1])/2):
                if prob > 0.10:
                    match_score = re.search(r'(\d{1,2})[:\-](\d{1,2})', text.strip())
                    if match_score:
                        score = f"{match_score.group(1)}:{match_score.group(2)}"
                        break

        except Exception as e:
            if debug:
                print(f"Erreur score match {i+1}: {e}")
            pass

        # === MT (zone sous le rectangle, partie centrale) ===
        try:
            mt_array = np.array(zone_mt)
            mt_pil = Image.fromarray(mt_array)
            enhancer = ImageEnhance.Contrast(mt_pil)
            mt_contraste = np.array(enhancer.enhance(3.0))

            res_mt = reader.readtext(mt_contraste, detail=1, paragraph=False)

            if debug:
                print(f"\n--- Match {i+1} MT ---")
                for bbox, text, prob in res_mt:
                    print(f"  '{text}' | prob: {prob:.2f}")

            for bbox, text, prob in res_mt:
                if prob > 0.10:
                    # MT explicite
                    match_mt = re.search(r'MT[:\s]*(\d{1,2})[:\-\.](\d{1,2})', text, re.IGNORECASE)
                    if match_mt:
                        mt = f"{match_mt.group(1)}:{match_mt.group(2)}"
                        break
                    # Fallback: score simple sans MT
                    match_simple = re.search(r'(\d{1,2})[:\-\.](\d{1,2})', text)
                    if match_simple and not mt:
                        candidate = f"{match_simple.group(1)}:{match_simple.group(2)}"
                        if candidate != score:  # Ne pas confondre avec le score final
                            mt = candidate

        except Exception as e:
            if debug:
                print(f"Erreur MT match {i+1}: {e}")
            pass

        # === NOM ÉQUIPE DOMICILE (zone nom gauche - HAUT) ===
        try:
            nom_g_array = np.array(zone_nom_gauche)
            nom_g_pil = Image.fromarray(nom_g_array)
            enhancer = ImageEnhance.Contrast(nom_g_pil)
            nom_g_contraste = np.array(enhancer.enhance(2.5))

            res_nom_g = reader.readtext(nom_g_contraste, detail=1, paragraph=False)

            if debug:
                print(f"\n--- Match {i+1} NOM GAUCHE ---")
                for bbox, text, prob in res_nom_g:
                    print(f"  '{text}' | prob: {prob:.2f}")

            noms_gauche = []
            for bbox, text, prob in res_nom_g:
                if prob > 0.20 and len(text) > 2 and not re.match(r'^\d+$', text):
                    text_propre = text.strip()
                    # Éliminer les minutes qui pourraient être dans la zone haute
                    if not re.search(r"\d+\s*['′]", text_propre):
                        noms_gauche.append(text_propre)

            if noms_gauche:
                equipe_dom = get_close_matches(noms_gauche[-1], engine.teams_list, n=1, cutoff=0.30)
                equipe_dom = equipe_dom[0] if equipe_dom else noms_gauche[-1]
                if debug:
                    print(f"  Équipe dom: {equipe_dom}")
        except Exception as e:
            if debug:
                print(f"Erreur nom gauche match {i+1}: {e}")
            pass

        # === NOM ÉQUIPE EXTÉRIEUR (zone nom droite - HAUT) ===
        try:
            nom_d_array = np.array(zone_nom_droite)
            nom_d_pil = Image.fromarray(nom_d_array)
            enhancer = ImageEnhance.Contrast(nom_d_pil)
            nom_d_contraste = np.array(enhancer.enhance(2.5))

            res_nom_d = reader.readtext(nom_d_contraste, detail=1, paragraph=False)

            if debug:
                print(f"\n--- Match {i+1} NOM DROITE ---")
                for bbox, text, prob in res_nom_d:
                    print(f"  '{text}' | prob: {prob:.2f}")

            noms_droite = []
            for bbox, text, prob in res_nom_d:
                if prob > 0.20 and len(text) > 2 and not re.match(r'^\d+$', text):
                    text_propre = text.strip()
                    if not re.search(r"\d+\s*['′]", text_propre):
                        noms_droite.append(text_propre)

            if noms_droite:
                equipe_ext = get_close_matches(noms_droite[-1], engine.teams_list, n=1, cutoff=0.30)
                equipe_ext = equipe_ext[0] if equipe_ext else noms_droite[-1]
                if debug:
                    print(f"  Équipe ext: {equipe_ext}")
        except Exception as e:
            if debug:
                print(f"Erreur nom droite match {i+1}: {e}")
            pass

        def extraire_minutes(zone_img, label="", debug=False):
            """Extrait les minutes de buteurs depuis une zone image.
            Gère les apostrophes manquantes (fallback chiffres 1-120)."""
            try:
                arr = np.array(zone_img)
                pil = Image.fromarray(arr)

                # Ajouter du padding blanc autour pour éviter que les chiffres
                # aux bords soient ignorés par EasyOCR
                pad = 20
                pil_padded = Image.new("RGB", (pil.width + pad*2, pil.height + pad*2), (255, 255, 255))
                pil_padded.paste(pil, (pad, pad))

                # Agrandir x3 pour améliorer la lisibilité
                pil_big = pil_padded.resize((pil_padded.width * 3, pil_padded.height * 3), Image.LANCZOS)
                enhanced = np.array(ImageEnhance.Contrast(pil_big).enhance(2.5))

                res = reader.readtext(enhanced, detail=1, paragraph=False)

                if debug:
                    print(f"\n--- {label} ---")
                    for bbox, text, prob in res:
                        print(f"  '{text}' | prob: {prob:.2f}")

                minutes = []
                texte_concat = ""

                for bbox, text, prob in res:
                    if prob > 0.08:
                        t = text.strip()
                        texte_concat += " " + t

                        # Priorité 1: chiffres suivis d'apostrophe (toutes variantes)
                        mins = re.findall(r"(\d{1,3})\s*['\u2019\u02bc\u0060\u00b4\u2018′‛`´]", t)
                        if mins:
                            minutes.extend(mins)
                            continue

                        # Priorité 2: fallback — tous les chiffres 1-120 dans la zone
                        # (dans la zone buteurs, les chiffres = minutes à coup sûr)
                        mins_fb = re.findall(r'\b(\d{1,3})\b', t)
                        for m in mins_fb:
                            if 1 <= int(m) <= 120:
                                minutes.append(m)

                # Dédoublonner en gardant l'ordre
                seen = set()
                minutes_uniq = []
                for m in minutes:
                    if m not in seen:
                        seen.add(m)
                        minutes_uniq.append(m)

                result = ' '.join(f"{m}'" for m in minutes_uniq)
                if debug and result:
                    print(f"  → Résultat: {result}")
                return result
            except Exception as e:
                if debug:
                    print(f"  Erreur: {e}")
                return ""

        # === BUTEURS DOMICILE ===
        buteurs_dom = extraire_minutes(zone_but_gauche, f"BUT GAUCHE M{i+1}", debug)

        # === BUTEURS EXTÉRIEUR ===
        buteurs_ext = extraire_minutes(zone_but_droite, f"BUT DROITE M{i+1}", debug)

        matches.append({
            'h': equipe_dom,
            'a': equipe_ext,
            's': score,
            'mt': mt,
            'hm': buteurs_dom,
            'am': buteurs_ext,
            'ligne_img': ligne_img
        })

    return matches


# ===================== HEADER & SAISON =====================
st.markdown(f"""
<div class="main-header">
    <div style="display:flex;align-items:center;gap:16px;">
        <!-- LOGO PNG -->
        <img src="data:image/png;base64,{LOGO_PNG_B64}"
             style="height:72px;width:auto;flex-shrink:0;filter:drop-shadow(0 0 10px #00FF88);" />
        <!-- TITRE + SOUS-TITRE -->
        <div style="flex:1;">
            <div style="display:flex;align-items:baseline;gap:14px;">
                <span style="font-family:'Orbitron',sans-serif;font-size:2.1em;font-weight:900;
                    color:#7FFFD4;letter-spacing:3px;text-shadow:0 0 20px #00FF88,0 0 40px rgba(0,255,136,.5);">
                    ORACLE MAHITA
                </span>
                <span style="font-family:'Orbitron',sans-serif;font-size:1.1em;font-weight:700;
                    color:#00FF88;letter-spacing:1px;">V53.0</span>
            </div>
            <div style="color:#aaa;font-size:0.85em;letter-spacing:2px;margin-top:3px;">
                IA Intégrée &middot; Apprentissage Actif
            </div>
        </div>
        <!-- DIAGNOSTICS PANEL -->
        <div style="background:#0a1a12;border:1px solid #1a3a2a;border-radius:10px;
             padding:10px 16px;min-width:185px;flex-shrink:0;">
            <div style="color:#7FFFD4;font-size:9px;font-weight:700;letter-spacing:2px;
                 text-transform:uppercase;margin-bottom:8px;text-align:center;">
                ⬡ Technical Diagnostics
            </div>
            <div style="display:flex;flex-direction:column;gap:5px;">
                <div style="display:flex;align-items:center;justify-content:space-between;">
                    <span style="color:#ccc;font-size:11px;">🧠 Cerveau Actif</span>
                    <span style="width:9px;height:9px;border-radius:50%;flex-shrink:0;
                        background:{'#00FF88' if CERVEAU_DISPONIBLE else '#FFA500'};
                        box-shadow:0 0 6px {'#00FF88' if CERVEAU_DISPONIBLE else '#FFA500'};"></span>
                </div>
                <div style="display:flex;align-items:center;justify-content:space-between;">
                    <span style="color:#ccc;font-size:11px;">⚙️ IA apprentissage</span>
                    <span style="width:9px;height:9px;border-radius:50%;flex-shrink:0;
                        background:{'#00FF88' if IA_DISPONIBLE else '#666'};
                        box-shadow:0 0 6px {'#00FF88' if IA_DISPONIBLE else 'transparent'};"></span>
                </div>
                <div style="display:flex;align-items:center;justify-content:space-between;">
                    <span style="color:#ccc;font-size:11px;">💬 Chat IA</span>
                    <span style="width:9px;height:9px;border-radius:50%;flex-shrink:0;
                        background:{'#00FF88' if CHAT_IA_DISPONIBLE else '#666'};
                        box-shadow:0 0 6px {'#00FF88' if CHAT_IA_DISPONIBLE else 'transparent'};"></span>
                </div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
s_active = st.selectbox("Saison", list(st.session_state['history'].keys()), label_visibility="collapsed")
st.session_state['s_active'] = s_active

days = [int(re.search(r'\d+', k).group()) for k in st.session_state['history'][s_active].keys() 
        if re.search(r'\d+', k) and st.session_state['history'][s_active][k].get("res")]
next_j = max(days) + 1 if days else 1
st.markdown(f'<div class="next-day-box">PROCHAINE JOURNÉE : J-{next_j}</div>', unsafe_allow_html=True)

tabs = st.tabs(["🏆 CLASSEMENT", "📅 CALENDRIER", "🎯 PRONOS", "⚽ RÉSULTATS", 
                "📚 HISTORIQUE", "⚙️ GESTION", "📊 PERFORMANCE", "🤖 ASSISTANT IA"])

# ===================== TAB 0 : CLASSEMENT =====================
with tabs[0]:
    st.markdown("### 🏆 Classement de la Saison")
    standings = get_standings(st.session_state['history'][s_active], engine.teams_list)

    def style_classement(row):
        rang = row['Rang']
        if 1 <= rang <= 5:
            return ['background-color: rgba(255,75,75,0.10)'] * len(row)  # Rouge transparent
        elif 6 <= rang <= 10:
            return ['background-color: rgba(75,150,255,0.10)'] * len(row)  # Bleu transparent
        elif 11 <= rang <= 15:
            return ['background-color: rgba(75,255,150,0.10)'] * len(row)  # Vert transparent
        elif 16 <= rang <= 20:
            return ['background-color: rgba(255,105,180,0.10)'] * len(row)  # Rose transparent
        return [''] * len(row)

    st.dataframe(standings.style.apply(style_classement, axis=1), use_container_width=True, hide_index=True)
    st.caption("🔴 Top 5 (Titre) · 🔵 6-10 · 🟢 11-15 · 🩷 16-20 (Relégation)")
# ===================== TAB 1 : CALENDRIER =====================
with tabs[1]:
    st.markdown("### 📅 Import du Calendrier")
    j_cal = st.number_input("Journée", 1, 50, next_j, key="j_cal_input")

    # ── Option OCR Bet261 ──
    st.markdown("#### 📸 Import par OCR (Bet261)")

    uploaded_file = st.file_uploader(
        "📷 Capture d'écran Bet261", 
        type=['jpg', 'jpeg', 'png'],
        key="ocr_cal_upload"
    )

    if uploaded_file is not None:
        img = Image.open(io.BytesIO(uploaded_file.getvalue()))
        st.image(img, caption="Image originale", use_container_width=True)

        if st.button("🔍 Lancer le scan OCR", use_container_width=True, key="btn_ocr_cal"):
            with st.spinner("Analyse avancée en cours..."):
                try:
                    matchs_ocr = ocr_calendrier_bet261(uploaded_file.getvalue())

                    if len(matchs_ocr) == 0:
                        st.error("❌ Aucun match détecté. Essayez la saisie manuelle.")
                    else:
                        st.success(f"✅ {len(matchs_ocr)} matchs détectés !")
                        st.session_state['ocr_matchs'] = matchs_ocr
                        st.session_state['ocr_img_cal'] = img
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")

        # ═══ ÉTAPE 2 : VÉRIFICATION ET CORRECTION ═══
        if 'ocr_matchs' in st.session_state:
            st.markdown("#### 📝 Vérifier et corriger les matchs")

            matchs_ocr = st.session_state['ocr_matchs']

            # Vérification doublons (uniquement pour avertir, pas bloquer)
            toutes_equipes = []
            for m in matchs_ocr:
                if m['h']: toutes_equipes.append(m['h'])
                if m['a']: toutes_equipes.append(m['a'])

            equipes_uniques = set(toutes_equipes)
            doublons = len(toutes_equipes) - len(equipes_uniques)

            if len(matchs_ocr) != 10:
                st.warning(f"⚠️ {len(matchs_ocr)} matchs trouvés sur 10 attendus.")

            if doublons > 0:
                st.warning(f"⚠️ {doublons} doublons d'équipes détectés. Corrigez ci-dessous.")

            if len(equipes_uniques) != 20:
                manquantes = [t for t in engine.teams_list if t not in equipes_uniques]
                if manquantes:
                    st.info(f"ℹ️ Équipes non détectées : {', '.join(manquantes)}")

            # Afficher les matchs
            for i, match in enumerate(matchs_ocr):
                is_deduit = not match['h'] or not match['a'] or any(c is None for c in match['o'])
                titre = f"⚽ Match {i+1}" + (" 🧠 (à vérifier)" if is_deduit else "")

                with st.expander(titre, expanded=(i==0 or is_deduit)):
                    cols = st.columns([1, 2])

                    with cols[0]:
                        if 'ligne_img' in match:
                            st.image(match['ligne_img'], use_container_width=True)

                    with cols[1]:
                        if is_deduit:
                            st.info("🧠 Certaines valeurs ont été déduites ou sont manquantes - vérifiez !")

                        # Toutes les équipes disponibles pour chaque match (pas de filtrage)
                        equipe_dom = st.selectbox(
                            "Domicile",
                            engine.teams_list,
                            index=engine.teams_list.index(match['h']) if match['h'] in engine.teams_list else 0,
                            key=f"ocr_dom_{i}"
                        )

                        equipe_ext = st.selectbox(
                            "Extérieur",
                            engine.teams_list,
                            index=engine.teams_list.index(match['a']) if match['a'] in engine.teams_list else 0,
                            key=f"ocr_ext_{i}"
                        )

                        c1, c2, c3 = st.columns(3)

                        def_c1 = match['o'][0] if match['o'][0] else 1.80
                        def_cx = match['o'][1] if match['o'][1] else 3.50
                        def_c2 = match['o'][2] if match['o'][2] else 4.00

                        cote_1 = c1.number_input(
                            "Cote 1", 
                            value=float(def_c1),
                            min_value=1.0, max_value=20.0, step=0.01,
                            key=f"ocr_c1_{i}"
                        )
                        cote_x = c2.number_input(
                            "Cote X", 
                            value=float(def_cx),
                            min_value=1.0, max_value=20.0, step=0.01,
                            key=f"ocr_cx_{i}"
                        )
                        cote_2 = c3.number_input(
                            "Cote 2", 
                            value=float(def_c2),
                            min_value=1.0, max_value=20.0, step=0.01,
                            key=f"ocr_c2_{i}"
                        )

                        if cote_1 > 10 or cote_2 > 10:
                            st.warning("⚠️ Cote élevée - vérifiez")

                        matchs_ocr[i] = {
                            'h': equipe_dom,
                            'a': equipe_ext,
                            'o': [cote_1, cote_x, cote_2]
                        }

            # Validation avec vérification stricte des doublons
            if st.button("🔥 Valider et importer", use_container_width=True, key="btn_valider_cal"):
                if len(matchs_ocr) != 10:
                    st.error(f"❌ Il faut exactement 10 matchs !")
                else:
                    toutes_equipes = []
                    for m in matchs_ocr:
                        toutes_equipes.extend([m['h'], m['a']])

                    if len(toutes_equipes) != len(set(toutes_equipes)):
                        # Identifier les doublons pour aider la correction
                        from collections import Counter
                        counts = Counter(toutes_equipes)
                        doublons_list = [eq for eq, c in counts.items() if c > 1]
                        st.error(f"❌ Doublons d'équipes détectés : {', '.join(doublons_list)} ! Corrigez dans les matchs concernés.")
                    else:
                        jk = f"Journée {j_cal}"
                        if jk not in st.session_state['history'][s_active]:
                            st.session_state['history'][s_active][jk] = {"cal": [], "res": [], "pro": []}

                        st.session_state['history'][s_active][jk]["cal"] = matchs_ocr
                        st.session_state['current_ready'] = matchs_ocr
                        st.session_state['current_j_num'] = j_cal
                        save_db(st.session_state['history'])

                        for key in ['ocr_matchs', 'ocr_img_cal']:
                            if key in st.session_state:
                                del st.session_state[key]

                        # Notification riche calendrier OCR
                        n_matchs = len(matchs_ocr)
                        equipes_str = ", ".join(f"{m['h']} vs {m['a']}" for m in matchs_ocr[:3])
                        if n_matchs > 3: equipes_str += f" (+ {n_matchs-3} autres)"
                        st.markdown(f"""
                        <div style="padding:16px;border:2px solid #7FFFD4;border-radius:12px;
                             background:rgba(127,255,212,0.07);margin:12px 0;">
                          <div style="color:#7FFFD4;font-weight:800;font-size:1.1em;margin-bottom:8px;">
                            ✅ Journée {j_cal} — Calendrier enregistré !
                          </div>
                          <div style="color:#ccc;font-size:13px;margin-bottom:6px;">
                            📋 <b>{n_matchs} matchs</b> importés avec succès
                          </div>
                          <div style="color:#aaa;font-size:12px;margin-bottom:10px;">{equipes_str}</div>
                          <div style="display:flex;gap:8px;flex-wrap:wrap;">
                            <span style="background:rgba(127,255,212,0.15);color:#7FFFD4;
                                  border-radius:6px;padding:4px 10px;font-size:12px;">
                              🎯 Allez dans PRONOS pour analyser
                            </span>
                            <span style="background:rgba(127,255,212,0.15);color:#7FFFD4;
                                  border-radius:6px;padding:4px 10px;font-size:12px;">
                              🧠 IA prête à prédire
                            </span>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.rerun()

    # ── Option 2 : Saisie manuelle ──
    st.divider()
    st.markdown("#### ✏️ Option 2 : Saisie manuelle")

    if 'tmp_cal' not in st.session_state:
        if st.button("➕ Initialiser saisie manuelle (10 matchs)", key="btn_init_cal"):
            st.session_state['tmp_cal'] = [
                {'h': engine.teams_list[i*2], 'a': engine.teams_list[i*2+1], 'o': [1.80, 3.50, 4.00]}
                for i in range(10)
            ]

    if 'tmp_cal' in st.session_state:
        with st.form("form_cal"):
            st.markdown("#### Vérifiez les matchs de la journée")
            final_c = []
            for i, m in enumerate(st.session_state['tmp_cal']):
                c1, c2, o1, ox, o2 = st.columns([2, 2, 1, 1, 1])
                th = c1.selectbox(f"Domicile {i+1}", engine.teams_list, index=engine.teams_list.index(m['h']) if m['h'] in engine.teams_list else 0, key=f"h_{i}")
                ta = c2.selectbox(f"Extérieur {i+1}", engine.teams_list, index=engine.teams_list.index(m['a']) if m['a'] in engine.teams_list else 0, key=f"a_{i}")
                c1v = o1.number_input("Cote 1", value=float(m['o'][0]), min_value=1.0, step=0.05, key=f"o1_{i}")
                cxv = ox.number_input("Cote X", value=float(m['o'][1]), min_value=1.0, step=0.05, key=f"ox_{i}")
                c2v = o2.number_input("Cote 2", value=float(m['o'][2]), min_value=1.0, step=0.05, key=f"o2_{i}")
                final_c.append({'h': th, 'a': ta, 'o': [c1v, cxv, c2v]})
            if st.form_submit_button("🔥 Valider & Enregistrer Calendrier"):
                jk = f"Journée {j_cal}"
                if jk not in st.session_state['history'][s_active]:
                    st.session_state['history'][s_active][jk] = {"cal": [], "res": [], "pro": []}
                st.session_state['history'][s_active][jk]["cal"] = final_c
                st.session_state['current_ready'] = final_c
                st.session_state['current_j_num'] = j_cal
                save_db(st.session_state['history'])
                if 'tmp_cal' in st.session_state: del st.session_state['tmp_cal']
                n_matchs_m = len(final_c)
                st.markdown(f"""
                <div style="padding:16px;border:2px solid #7FFFD4;border-radius:12px;
                     background:rgba(127,255,212,0.07);margin:12px 0;">
                  <div style="color:#7FFFD4;font-weight:800;font-size:1.1em;margin-bottom:6px;">
                    ✅ Journée {j_cal} — Calendrier enregistré !
                  </div>
                  <div style="color:#ccc;font-size:13px;">📋 <b>{n_matchs_m} matchs</b> saisis manuellement</div>
                  <div style="color:#888;font-size:12px;margin-top:8px;">➡️ Rendez-vous dans l'onglet <b>PRONOS</b></div>
                </div>
                """, unsafe_allow_html=True)
                st.rerun()

# ===================== TAB 2 : PRONOS =====================
with tabs[2]:
    st.markdown("### 🎯 Pronostics — Analyse Multi-Moteurs")

    if 'current_ready' not in st.session_state or not st.session_state.get('current_ready'):
        st.info("Veuillez d'abord enregistrer un calendrier dans l'onglet **CALENDRIER**.")
    else:
        current_ready = st.session_state['current_ready']
        j_num = st.session_state.get('current_j_num', 1)
        standings = get_standings(st.session_state['history'][s_active], engine.teams_list)

        # Récupérer les stats IA apprentissage
        stats_ia = moteur_apprentissage.get_stats_apprentissage() if IA_DISPONIBLE else {}
        patterns_cotes = moteur_apprentissage.patterns if IA_DISPONIBLE else {}

        safe_d, risque_d, fun_d = [], [], []
        all_analyses = []

        for idx, m in enumerate(current_ready):
            r_dom = int(standings[standings['Équipe'] == m['h']]['Rang'].values[0]) if not standings[standings['Équipe'] == m['h']].empty else 10
            r_ext = int(standings[standings['Équipe'] == m['a']]['Rang'].values[0]) if not standings[standings['Équipe'] == m['a']].empty else 10

            forme_dom = get_forme_equipe(st.session_state['history'], s_active, m['h'])
            forme_ext = get_forme_equipe(st.session_state['history'], s_active, m['a'])
            serie_dom = get_serie_victoires(forme_dom)
            serie_ext = get_serie_victoires(forme_ext)
            dernier_adv = get_dernier_adversaire(st.session_state['history'], s_active, m['h'])

            # ═══ MOTEUR 1: Cerveau I ═══
            analyse_cerveau = None
            if oracle_brain:
                analyse_cerveau = oracle_brain.analyser_match(
                    equipe_dom=m['h'], equipe_ext=m['a'], cotes=m['o'],
                    journee=j_num, rang_dom=r_dom, rang_ext=r_ext,
                    serie_dom=serie_dom, serie_ext=serie_ext,
                    forme_dom=forme_dom, forme_ext=forme_ext,
                    match_precedent_dom=dernier_adv
                )

            # ═══ MOTEUR 2: IA Apprentissage V2.3 ═══
            prediction_ia = None
            confiance_ia = 50
            details_ia = "Non dispo"

            if IA_DISPONIBLE and moteur_apprentissage is not None:
                try:
                    _f_dom_ia = get_forme_equipe(st.session_state['history'], s_active, m['h'], 3)
                    _f_ext_ia = get_forme_equipe(st.session_state['history'], s_active, m['a'], 3)
                    def _buts_ia(eq, dom=True):
                        bp, bc, n = [], [], 0
                        for _jd in st.session_state['history'][s_active].values():
                            for _mr in _jd.get("res", []):
                                try:
                                    _s, _a = map(int, _mr['s'].replace('-',':').split(':'))
                                    if dom and _mr['h']==eq: bp.append(_s); bc.append(_a); n+=1
                                    elif not dom and _mr['a']==eq: bp.append(_a); bc.append(_s); n+=1
                                except: pass
                        return (sum(bp)/n if n else 1.5, sum(bc)/n if n else 1.5)
                    _bpmd, _bcmd = _buts_ia(m['h'], True)
                    _bpme, _bcme = _buts_ia(m['a'], False)
                    _tad = "favori" if r_dom<=5 else ("medium" if r_dom<=15 else "outsider")
                    _tae = "favori" if r_ext<=5 else ("medium" if r_ext<=15 else "outsider")
                    _ctx_ia = {
                        "rang_dom": r_dom, "rang_ext": r_ext,
                        "serie_dom": _f_dom_ia, "serie_ext": _f_ext_ia,
                        "evolution_dom": "stable", "evolution_ext": "stable",
                        "bp_moy_dom": _bpmd, "bc_moy_dom": _bcmd,
                        "bp_moy_ext": _bpme, "bc_moy_ext": _bcme,
                        "type_adv_dom": _tad, "type_adv_ext": _tae,
                        "prob_forme": {"1": 33.3, "X": 33.3, "2": 33.3}
                    }
                    if hasattr(moteur_apprentissage, 'predire_avec_apprentissage'):
                        _pred = moteur_apprentissage.predire_avec_apprentissage(
                            {"h": m['h'], "a": m['a'], "o": m['o']}, _ctx_ia)
                        prediction_ia = _pred["prediction"]
                        confiance_ia = int(_pred["confiance"])
                    elif moteur_apprentissage.patterns:
                        _c1p, _cxp, _c2p = m['o']
                        for _pk, _pd in moteur_apprentissage.patterns.items():
                            if isinstance(_pd, dict) and _pd.get("total",0) >= 3:
                                try:
                                    _pc1,_pcx,_pc2 = map(float, _pk.split('_'))
                                    if abs(_pc1-_c1p)+abs(_pcx-_cxp)+abs(_pc2-_c2p) < 1.5:
                                        _tot = _pd["total"]
                                        _p1 = _pd.get("1",0)/_tot; _px = _pd.get("X",0)/_tot; _p2 = _pd.get("2",0)/_tot
                                        if _p1>_px and _p1>_p2: prediction_ia="1"; confiance_ia=int(_p1*100)
                                        elif _p2>_p1 and _p2>_px: prediction_ia="2"; confiance_ia=int(_p2*100)
                                        else: prediction_ia="X"; confiance_ia=int(_px*100)
                                        break
                                except: continue
                    if prediction_ia:
                        details_ia = f"{prediction_ia} ({confiance_ia}%)"
                except Exception as _e_ia:
                    details_ia = f"Erreur IA: {str(_e_ia)[:30]}"


            # ═══ MOTEUR 3: Analyse statistique (cotes + classement + forme) ═══
            cote_1, cote_x, cote_2 = m['o']

            force_1 = 1 / cote_1
            force_x = 1 / cote_x
            force_2 = 1 / cote_2

            diff_rang = r_ext - r_dom
            force_1 += diff_rang * 0.015
            force_2 -= diff_rang * 0.015

            if forme_dom:
                pts_dom = sum(3 if r == "V" else (1 if r == "N" else 0) for r in forme_dom[-5:])
                force_1 += pts_dom * 0.01
            if forme_ext:
                pts_ext = sum(3 if r == "V" else (1 if r == "N" else 0) for r in forme_ext[-5:])
                force_2 += pts_ext * 0.01

            force_1 += serie_dom * 0.02
            force_2 += serie_ext * 0.02

            total_force = force_1 + force_x + force_2
            prob_1 = force_1 / total_force
            prob_x = force_x / total_force
            prob_2 = force_2 / total_force

            if prob_1 > prob_x and prob_1 > prob_2:
                prediction_stats = "1"
                confiance_stats = int(prob_1 * 100)
            elif prob_2 > prob_1 and prob_2 > prob_x:
                prediction_stats = "2"
                confiance_stats = int(prob_2 * 100)
            else:
                prediction_stats = "X"
                confiance_stats = int(prob_x * 100)

            # ═══ FUSION DES MOTEURS ═══
            predictions = []
            confiances = []

            if analyse_cerveau:
                pred_cerv = "1" if "1" in analyse_cerveau.get('choix_expert', '') else (
                    "2" if "2" in analyse_cerveau.get('choix_expert', '') else "X"
                )
                predictions.append(pred_cerv)
                confiances.append(analyse_cerveau.get('indice_confiance', 50))

            if prediction_ia:
                predictions.append(prediction_ia)
                confiances.append(confiance_ia)

            predictions.append(prediction_stats)
            confiances.append(confiance_stats)

            from collections import Counter
            vote = Counter(predictions)
            prediction_finale = vote.most_common(1)[0][0]

            confiance_finale = int(sum(confiances) / len(confiances))

            if len(set(predictions)) == 1:
                confiance_finale = min(95, confiance_finale + 15)
            elif len(set(predictions)) == 2:
                confiance_finale = max(40, confiance_finale - 10)

            # ═══ CALCUL SCORE PROBABLE ═══
            if prediction_finale == "1":
                buts_dom = max(1, round(prob_1 * 4))
                buts_ext = max(0, round(prob_2 * 2))
            elif prediction_finale == "2":
                buts_dom = max(0, round(prob_1 * 2))
                buts_ext = max(1, round(prob_2 * 4))
            else:
                buts_dom = max(1, round(prob_1 * 2.5))
                buts_ext = buts_dom

            if forme_dom and "V" in forme_dom[-3:]:
                buts_dom += 1
            if forme_ext and "V" in forme_ext[-3:]:
                buts_ext += 1

            buts_dom = min(buts_dom, 5)
            buts_ext = min(buts_ext, 5)

            score_probable = f"{buts_dom}-{buts_ext}"

            # ═══ CHOIX EXPERT FINAL ═══
            if prediction_finale == "1":
                choix_final = f"{m['h']} (cote {cote_1})"
                cote_choix = cote_1
            elif prediction_finale == "2":
                choix_final = f"{m['a']} (cote {cote_2})"
                cote_choix = cote_2
            else:
                choix_final = f"Nul (cote {cote_x})"
                cote_choix = cote_x

            if confiance_finale >= 75:
                confiance_label = "BANKER"
            elif confiance_finale >= 55:
                confiance_label = "RISQUE CALCULÉ"
            else:
                confiance_label = "FUN"

            analyse_finale = {
                'choix_expert': choix_final,
                'indice_confiance': confiance_finale,
                'confiance': confiance_label,
                'score_probable': score_probable,
                'prediction': prediction_finale,
                'r_dom': r_dom,
                'r_ext': r_ext,
                'details_moteurs': {
                    'cerveau': (analyse_cerveau.get('choix_expert', 'N/A') + (" (Inline)" if not CERVEAU_DISPONIBLE else "")) if analyse_cerveau else 'Non dispo',
                    'ia': details_ia,
                    'stats': f"{prediction_stats} ({confiance_stats}%)"
                }
            }

            all_analyses.append((m, analyse_finale))

            item = {
                "match": f"{m['h']} vs {m['a']}",
                "choix": choix_final,
                "score": score_probable,
                "cote": cote_choix,
                "indice": confiance_finale,
                "prediction": prediction_finale
            }

            if confiance_label == "BANKER":
                safe_d.append(item)
            elif confiance_label == "RISQUE CALCULÉ":
                risque_d.append(item)
            else:
                fun_d.append(item)

        # Affichage des analyses
        st.markdown(f"**Journée {j_num}** — {len(current_ready)} matchs analysés par multi-moteurs")

        for idx, (m, analyse) in enumerate(all_analyses):
            with st.container():
                st.markdown(f"**⚽ Match {idx+1} : {m['h']} vs {m['a']}**")

                col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

                with col1:
                    st.markdown("📊 **Cotes**")
                    st.caption(f"1: {m['o'][0]} | X: {m['o'][1]} | 2: {m['o'][2]}")
                    st.caption(f"Classement: {m['h']} #{analyse['r_dom']} vs {m['a']} #{analyse['r_ext']}")

                with col2:
                    st.markdown("🧠 **Prédiction**")
                    color_conf = "#00FF00" if analyse['confiance'] == "BANKER" else (
                        "#FFA500" if analyse['confiance'] == "RISQUE CALCULÉ" else "#FF4B4B"
                    )
                    st.markdown(f"<span style='color:{color_conf};font-weight:bold;'>{analyse['confiance']}</span>", unsafe_allow_html=True)
                    st.markdown(f"**{analyse['choix_expert']}**")
                    st.caption(f"Confiance: {analyse['indice_confiance']}%")

                with col3:
                    st.markdown("⚽ **Score Probable**")
                    st.markdown(f"""<div style='text-align:center;padding:12px 8px;
                        background:rgba(127,255,212,0.15);border-radius:8px;
                        border:2px solid #7FFFD4;margin-top:4px;'>
                        <span style='font-size:2em;font-weight:bold;color:#7FFFD4;'>
                        {analyse['score_probable']}</span></div>""", unsafe_allow_html=True)

                with col4:
                    st.markdown("🔍 **Détails Moteurs**")
                    details = analyse['details_moteurs']
                    st.caption(f"Cerveau: {details['cerveau']}")
                    st.caption(f"IA: {details['ia']}")
                    st.caption(f"Stats: {details['stats']}")

                conf = analyse['indice_confiance']
                st.progress(conf, text=f"Indice de confiance global: {conf}%")

            st.divider()

        # Sauvegarde pronos
        jk = f"Journée {j_num}"
        if jk in st.session_state['history'][s_active]:
            st.session_state['history'][s_active][jk]["pro"] = [
                {
                    "m": a['choix_expert'],
                    "c": m['o'],
                    "indice": a['indice_confiance'],
                    "classe": a['confiance'],
                    "score": a['score_probable'],
                    "prediction": a['prediction']
                }
                for m, a in all_analyses
            ]
            save_db(st.session_state['history'])

        # Tickets
        st.markdown("---")
        st.markdown("### 🎫 Tickets recommandés")

        c1, c2, c3 = st.columns(3)

        def show_ticket(col, title, data, emoji, css):
            with col:
                st.markdown(f"### {emoji} {title}")
                if len(data) == 0:
                    st.info("Aucun match dans cette catégorie")
                    return

                total = 1.0
                for i, x in enumerate(data[:3]):
                    st.markdown(f"""
                    <div class='{css}' style='margin-bottom:10px;padding:10px;'>
                        <b>#{i+1} {x['match']}</b><br>
                        🎯 {x['choix']}<br>
                        ⚽ Score: <b>{x['score']}</b><br>
                        📊 Confiance: {x['indice']}%
                    </div>
                    """, unsafe_allow_html=True)
                    total *= x['cote']

                st.info(f"📈 Cote combinée: {total:.2f}")
                if len(data) > 3:
                    st.caption(f"+ {len(data)-3} autres matchs")

        show_ticket(c1, "TICKET SAFE", safe_d, "🟢", "prono-safe")
        show_ticket(c2, "TICKET RISQUE", risque_d, "🟡", "prono-risque")
        show_ticket(c3, "TICKET FUN", fun_d, "🔴", "prono-fun")

# ===================== TAB 3 : RÉSULTATS =====================
with tabs[3]:
    st.markdown("### ⚽ Saisie des Résultats")

    j_res = st.number_input("Journée", 1, 50, 1, key="j_res_input")
    
    # ── Option OCR Bet261 ──
    st.markdown("#### 📸 Import par OCR (Bet261)")
    
    f_res = st.file_uploader("📷 Capture d'écran Bet261", type=['jpg','png','jpeg'], key="res_upload")

    extracted = []
    jk = f"Journée {j_res}"
    cal_ref = st.session_state['history'][s_active].get(jk, {}).get("cal", [])

    if f_res:
        img = Image.open(io.BytesIO(f_res.getvalue()))
        st.image(img, caption="Image originale", use_container_width=True)

        if st.button("🔍 Lancer le scan OCR", use_container_width=True, key="btn_ocr_res"):
            with st.spinner("OCR avancé en cours..."):
                try:
                    extracted = ocr_resultats_bet261(f_res.getvalue())

                    if len(extracted) == 0:
                        st.error("❌ Aucun match détecté. Essayez la saisie manuelle.")
                    else:
                        st.success(f"✅ {len(extracted)} matchs détectés !")
                        st.session_state['ocr_res_matchs'] = extracted
                        st.session_state['ocr_res_img'] = img
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")

        # ═══ ÉTAPE 2 : VÉRIFICATION ET CORRECTION ═══
        if 'ocr_res_matchs' in st.session_state:
            st.markdown("#### 📝 Vérifier et corriger les résultats")

            extracted = st.session_state['ocr_res_matchs']

            # Compléter avec le calendrier si manquant
            if cal_ref and len(extracted) < len(cal_ref):
                known = {(m.get('h'), m.get('a')) for m in extracted}
                for cm in cal_ref:
                    if (cm['h'], cm['a']) not in known:
                        extracted.append({
                            "h": cm['h'], "a": cm['a'],
                            "s": "", "mt": "", "hm": "", "am": ""
                        })

            # Vérification
            if len(extracted) != 10:
                st.warning(f"⚠️ {len(extracted)} matchs trouvés sur 10 attendus.")

            # Afficher les matchs avec aperçu agrandi
            final_res = []
            for i, m in enumerate(extracted):
                is_deduit = not m.get('h') or not m.get('a') or not m.get('s')
                titre = f"⚽ Match {i+1}" + (" 🧠 (à vérifier)" if is_deduit else "")

                with st.expander(titre, expanded=(i==0 or is_deduit)):
                    cols = st.columns([1, 2])

                    with cols[0]:
                        # Afficher l'image de la ligne détectée
                        if 'ligne_img' in m and m['ligne_img']:
                            st.image(m['ligne_img'], use_container_width=True)
                        else:
                            st.info("Aperçu non disponible")

                    with cols[1]:
                        if is_deduit:
                            st.info("🧠 Certaines valeurs ont été déduites ou sont manquantes - vérifiez !")

                        # Équipes
                        equipe_dom = st.selectbox(
                            "Domicile",
                            engine.teams_list,
                            index=engine.teams_list.index(m['h']) if m['h'] in engine.teams_list else 0,
                            key=f"res_dom_{i}"
                        )
                        equipe_ext = st.selectbox(
                            "Extérieur",
                            engine.teams_list,
                            index=engine.teams_list.index(m['a']) if m['a'] in engine.teams_list else 0,
                            key=f"res_ext_{i}"
                        )

                        # Scores
                        col_s1, col_s2 = st.columns(2)
                        score = col_s1.text_input(
                            "Score Final (format X:Y)",
                            m.get('s', '0:0'),
                            key=f"res_score_{i}"
                        )
                        mt_score = col_s2.text_input(
                            "Mi-temps (format X:Y)",
                            m.get('mt', ''),
                            key=f"res_mt_{i}"
                        )

                        # Buteurs
                        col_b1, col_b2 = st.columns(2)
                        hm = col_b1.text_input(
                            f"Buteurs {equipe_dom} (ex: 24' 82')",
                            m.get('hm', ''),
                            key=f"res_hm_{i}"
                        )
                        am = col_b2.text_input(
                            f"Buteurs {equipe_ext} (ex: 41' 64')",
                            m.get('am', ''),
                            key=f"res_am_{i}"
                        )

                        final_res.append({
                            "h": equipe_dom,
                            "a": equipe_ext,
                            "s": score,
                            "mt": mt_score,
                            "hm": hm,
                            "am": am
                        })

            # Validation
            if st.button("✅ Enregistrer les résultats", use_container_width=True, key="btn_valider_res"):
                if len(final_res) != 10:
                    st.error(f"❌ Il faut exactement 10 matchs !")
                else:
                    if jk not in st.session_state['history'][s_active]:
                        st.session_state['history'][s_active][jk] = {"cal": cal_ref, "res": [], "pro": []}

                    st.session_state['history'][s_active][jk]["res"] = final_res
                    save_db(st.session_state['history'])

                    # ── Apprentissage IA V2.3 ──
                    if IA_DISPONIBLE and moteur_apprentissage is not None:
                        try:
                            _hav = {jj: st.session_state['history'][s_active][jj]
                                for jj in sorted(st.session_state['history'][s_active].keys())
                                if (int(re.search(r'\d+',jj).group()) if re.search(r'\d+',jj) else 0) < j_res}
                            _stav = get_standings(_hav, engine.teams_list)
                            _se = {t: {"bp_dom":[],"bc_dom":[],"bp_ext":[],"bc_ext":[]} for t in engine.teams_list}
                            for _jd in _hav.values():
                                for _mm in _jd.get("res",[]):
                                    try:
                                        _s,_a = map(int, _mm['s'].replace('-',':').split(':'))
                                        if _mm['h'] in _se: _se[_mm['h']]["bp_dom"].append(_s); _se[_mm['h']]["bc_dom"].append(_a)
                                        if _mm['a'] in _se: _se[_mm['a']]["bp_ext"].append(_a); _se[_mm['a']]["bc_ext"].append(_s)
                                    except: pass
                            def _moy_l(lst): return sum(lst)/len(lst) if lst else 1.5
                            for _i, _mm in enumerate(final_res):
                                try:
                                    _sh,_sa = map(int, _mm['s'].replace('-',':').split(':'))
                                    _res = "1" if _sh>_sa else ("X" if _sh==_sa else "2")
                                    _co = cal_ref[_i].get('o',[2.0,3.0,3.0]) if cal_ref and _i<len(cal_ref) else [2.0,3.0,3.0]
                                    _rd = int(_stav[_stav['Équipe']==_mm['h']]['Rang'].values[0]) if not _stav[_stav['Équipe']==_mm['h']].empty else 10
                                    _re = int(_stav[_stav['Équipe']==_mm['a']]['Rang'].values[0]) if not _stav[_stav['Équipe']==_mm['a']].empty else 10
                                    _fd = get_forme_equipe(st.session_state['history'], s_active, _mm['h'], 3)
                                    _fe = get_forme_equipe(st.session_state['history'], s_active, _mm['a'], 3)
                                    _bpmd=_moy_l(_se[_mm['h']]["bp_dom"]); _bcmd=_moy_l(_se[_mm['h']]["bc_dom"])
                                    _bpme=_moy_l(_se[_mm['a']]["bp_ext"]); _bcme=_moy_l(_se[_mm['a']]["bc_ext"])
                                    _tad="favori" if _rd<=5 else ("medium" if _rd<=15 else "outsider")
                                    _tae="favori" if _re<=5 else ("medium" if _re<=15 else "outsider")
                                    if hasattr(moteur_apprentissage,'analyser_pattern_cotes'):
                                        moteur_apprentissage.analyser_pattern_cotes(_co[0],_co[1],_co[2],_res)
                                    if hasattr(moteur_apprentissage,'analyser_pattern_classement'):
                                        moteur_apprentissage.analyser_pattern_classement(_mm['h'],_mm['a'],_rd,_re,_res)
                                    if hasattr(moteur_apprentissage,'analyser_pattern_force'):
                                        moteur_apprentissage.analyser_pattern_force(_mm['h'],_mm['a'],_rd,_re,_res)
                                    if hasattr(moteur_apprentissage,'analyser_pattern_lieu_rang'):
                                        moteur_apprentissage.analyser_pattern_lieu_rang(_mm['h'],_mm['a'],_rd,_re,_res)
                                    if hasattr(moteur_apprentissage,'analyser_pattern_serie_forme'):
                                        moteur_apprentissage.analyser_pattern_serie_forme(_mm['h'],_mm['a'],_fd,_fe,_res)
                                    if hasattr(moteur_apprentissage,'analyser_pattern_serie_rang'):
                                        moteur_apprentissage.analyser_pattern_serie_rang(_mm['h'],_mm['a'],"stable","stable",_res)
                                    if hasattr(moteur_apprentissage,'analyser_pattern_tendance_buts'):
                                        moteur_apprentissage.analyser_pattern_tendance_buts(_mm['h'],_mm['a'],_bpmd,_bcmd,_bpme,_bcme,_tad,_tae,_res)
                                    if hasattr(moteur_apprentissage,'analyser_pattern_equipe'):
                                        moteur_apprentissage.analyser_pattern_equipe(_mm['h'],"V" if _res=="1" else ("N" if _res=="X" else "D"),{"domicile":True})
                                        moteur_apprentissage.analyser_pattern_equipe(_mm['a'],"V" if _res=="2" else ("N" if _res=="X" else "D"),{"domicile":False})
                                    # ✅ V53.1 — Suivi précision IA : enregistrer_prediction avec résultat réel
                                    if hasattr(moteur_apprentissage, 'enregistrer_prediction'):
                                        # Récupérer le prono sauvegardé pour ce match si disponible
                                        _pro_j = st.session_state['history'][s_active].get(jk, {}).get("pro", [])
                                        _pred_saved = _pro_j[_i] if _i < len(_pro_j) else {}
                                        _prediction_ia = _pred_saved.get('prediction', None)
                                        _confiance_ia  = _pred_saved.get('indice', 50)
                                        _match_data = {"h": _mm['h'], "a": _mm['a'], "o": _co}
                                        _facteurs_ia = {
                                            "cote_favorite": "1" if _co[0] < _co[2] else "2",
                                            "classement":    "1" if _rd < _re else "2"
                                        }
                                        moteur_apprentissage.enregistrer_prediction(
                                            match_data=_match_data,
                                            prediction=_prediction_ia or ("1" if _co[0]<_co[2] else "2"),
                                            confiance=_confiance_ia,
                                            resultat_reel=_res,
                                            facteurs_utilises=_facteurs_ia
                                        )
                                except: pass
                            moteur_apprentissage.save()
                        except Exception as _e_ap: pass

                    # Nettoyer session
                    for key in ['ocr_res_matchs', 'ocr_res_img']:
                        if key in st.session_state:
                            del st.session_state[key]

                    # ── Notification riche résultats ──
                    nb_1r = nb_xr = nb_2r = buts_r = 0
                    victoires_dom, victoires_ext, nuls = [], [], []
                    for r in final_res:
                        try:
                            sh, sa = map(int, r['s'].replace('-',':').split(':'))
                            buts_r += sh + sa
                            if sh > sa: nb_1r += 1; victoires_dom.append(r['h'])
                            elif sh == sa: nb_xr += 1; nuls.append(f"{r['h']}-{r['a']}")
                            else: nb_2r += 1; victoires_ext.append(r['a'])
                        except: pass
                    st.markdown(f"""
                    <div style="padding:16px;border:2px solid #00FF00;border-radius:12px;
                         background:rgba(0,255,0,0.05);margin:12px 0;">
                      <div style="color:#00FF88;font-weight:800;font-size:1.1em;margin-bottom:10px;">
                        ✅ Journée {j_res} — Résultats enregistrés !
                      </div>
                      <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
                        <div style="background:rgba(0,255,0,0.1);border-radius:8px;padding:8px 14px;text-align:center;">
                          <div style="color:#00FF88;font-size:1.4em;font-weight:800;">{nb_1r}</div>
                          <div style="color:#888;font-size:11px;">Victoires Dom.</div>
                        </div>
                        <div style="background:rgba(255,165,0,0.1);border-radius:8px;padding:8px 14px;text-align:center;">
                          <div style="color:#FFA500;font-size:1.4em;font-weight:800;">{nb_xr}</div>
                          <div style="color:#888;font-size:11px;">Nuls</div>
                        </div>
                        <div style="background:rgba(127,255,212,0.1);border-radius:8px;padding:8px 14px;text-align:center;">
                          <div style="color:#7FFFD4;font-size:1.4em;font-weight:800;">{nb_2r}</div>
                          <div style="color:#888;font-size:11px;">Victoires Ext.</div>
                        </div>
                        <div style="background:rgba(255,255,255,0.05);border-radius:8px;padding:8px 14px;text-align:center;">
                          <div style="color:#fff;font-size:1.4em;font-weight:800;">{buts_r}</div>
                          <div style="color:#888;font-size:11px;">Buts total</div>
                        </div>
                      </div>
                      <div style="color:#aaa;font-size:12px;">
                        🧠 IA Apprentissage mis à jour · 🏆 Classement recalculé
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.rerun()

    # ── Option 2 : Saisie manuelle ──
    st.divider()
    st.markdown("#### ✏️ Saisie manuelle")

    if 'tmp_res' not in st.session_state:
        if st.button("➕ Initialiser saisie manuelle (10 matchs)", key="btn_init_res"):
            # Pré-remplir avec le calendrier si disponible
            if cal_ref and len(cal_ref) == 10:
                st.session_state['tmp_res'] = [
                    {"h": c['h'], "a": c['a'], "s": "0:0", "mt": "", "hm": "", "am": ""}
                    for c in cal_ref
                ]
            else:
                st.session_state['tmp_res'] = [
                    {"h": engine.teams_list[i*2 % 20], "a": engine.teams_list[(i*2+1) % 20], 
                     "s": "0:0", "mt": "", "hm": "", "am": ""}
                    for i in range(10)
                ]

    if 'tmp_res' in st.session_state:
        with st.form("form_resultats_manual"):
            st.markdown("#### Vérifiez les résultats")
            final_res_manual = []
            for i, m in enumerate(st.session_state['tmp_res']):
                st.markdown(f"**Match {i+1} : {m['h']} vs {m['a']}**")
                
                col1, col2 = st.columns(2)
                score = col1.text_input("Score Final (X:Y)", m['s'], key=f"man_score_{i}")
                mt = col2.text_input("Mi-temps (X:Y)", m['mt'], key=f"man_mt_{i}")
                
                col3, col4 = st.columns(2)
                hm = col3.text_input(f"Buteurs {m['h']}", m['hm'], key=f"man_hm_{i}")
                am = col4.text_input(f"Buteurs {m['a']}", m['am'], key=f"man_am_{i}")
                
                final_res_manual.append({
                    "h": m['h'], "a": m['a'],
                    "s": score, "mt": mt,
                    "hm": hm, "am": am
                })
                st.divider()
            
            if st.form_submit_button("✅ Enregistrer Résultats"):
                if jk not in st.session_state['history'][s_active]:
                    st.session_state['history'][s_active][jk] = {"cal": cal_ref, "res": [], "pro": []}
                
                st.session_state['history'][s_active][jk]["res"] = final_res_manual
                save_db(st.session_state['history'])

                # ── Apprentissage IA sur résultats manuels ──
                if IA_DISPONIBLE and moteur_apprentissage is not None:
                    try:
                        _hav2 = {jj: st.session_state['history'][s_active][jj]
                            for jj in sorted(st.session_state['history'][s_active].keys())
                            if (int(re.search(r'\d+',jj).group()) if re.search(r'\d+',jj) else 0) < j_res}
                        _stav2 = get_standings(_hav2, engine.teams_list)
                        _cal_m = st.session_state['history'][s_active].get(jk, {}).get("cal", [])
                        for _im, _mm in enumerate(final_res_manual):
                            try:
                                _sh2,_sa2 = map(int, _mm['s'].replace('-',':').split(':'))
                                _rm = "1" if _sh2>_sa2 else ("X" if _sh2==_sa2 else "2")
                                _com = _cal_m[_im].get('o',[2.0,3.0,3.0]) if _cal_m and _im<len(_cal_m) else [2.0,3.0,3.0]
                                _rdm = int(_stav2[_stav2['Équipe']==_mm['h']]['Rang'].values[0]) if not _stav2[_stav2['Équipe']==_mm['h']].empty else 10
                                _rem = int(_stav2[_stav2['Équipe']==_mm['a']]['Rang'].values[0]) if not _stav2[_stav2['Équipe']==_mm['a']].empty else 10
                                _fdm = get_forme_equipe(st.session_state['history'], s_active, _mm['h'], 3)
                                _fem = get_forme_equipe(st.session_state['history'], s_active, _mm['a'], 3)
                                if hasattr(moteur_apprentissage,'analyser_pattern_cotes'):
                                    moteur_apprentissage.analyser_pattern_cotes(_com[0],_com[1],_com[2],_rm)
                                if hasattr(moteur_apprentissage,'analyser_pattern_classement'):
                                    moteur_apprentissage.analyser_pattern_classement(_mm['h'],_mm['a'],_rdm,_rem,_rm)
                                if hasattr(moteur_apprentissage,'analyser_pattern_equipe'):
                                    moteur_apprentissage.analyser_pattern_equipe(_mm['h'],"V" if _rm=="1" else ("N" if _rm=="X" else "D"),{"domicile":True})
                                    moteur_apprentissage.analyser_pattern_equipe(_mm['a'],"V" if _rm=="2" else ("N" if _rm=="X" else "D"),{"domicile":False})
                                # ✅ V53.1 — Suivi précision IA
                                if hasattr(moteur_apprentissage, 'enregistrer_prediction'):
                                    _pro_j2 = st.session_state['history'][s_active].get(jk, {}).get("pro", [])
                                    _pred_s2 = _pro_j2[_im] if _im < len(_pro_j2) else {}
                                    _pred_ia2 = _pred_s2.get('prediction', None)
                                    _conf_ia2 = _pred_s2.get('indice', 50)
                                    moteur_apprentissage.enregistrer_prediction(
                                        match_data={"h": _mm['h'], "a": _mm['a'], "o": _com},
                                        prediction=_pred_ia2 or ("1" if _com[0]<_com[2] else "2"),
                                        confiance=_conf_ia2,
                                        resultat_reel=_rm,
                                        facteurs_utilises={
                                            "cote_favorite": "1" if _com[0] < _com[2] else "2",
                                            "classement":    "1" if _rdm < _rem else "2"
                                        }
                                    )
                            except: pass
                        moteur_apprentissage.save()
                    except: pass

                if 'tmp_res' in st.session_state:
                    del st.session_state['tmp_res']
                
                # Notification résultats manuel
                nb_1m = nb_xm = nb_2m = buts_m = 0
                for r in final_res_manual:
                    try:
                        sh, sa = map(int, r['s'].replace('-',':').split(':'))
                        buts_m += sh + sa
                        if sh > sa: nb_1m += 1
                        elif sh == sa: nb_xm += 1
                        else: nb_2m += 1
                    except: pass
                st.markdown(f"""
                <div style="padding:14px;border:2px solid #00FF00;border-radius:12px;
                     background:rgba(0,255,0,0.05);margin:10px 0;">
                  <div style="color:#00FF88;font-weight:800;margin-bottom:8px;">
                    ✅ Journée {j_res} — Résultats enregistrés !
                  </div>
                  <div style="color:#ccc;font-size:13px;">
                    🏠 Dom: {nb_1m} · 🤝 Nul: {nb_xm} · ✈️ Ext: {nb_2m} · ⚽ Buts: {buts_m}
                  </div>
                </div>
                """, unsafe_allow_html=True)
                st.rerun()

# ===================== TAB 4 : HISTORIQUE =====================
with tabs[4]:
    st.markdown("### 📚 Historique des Journées")

    sorted_j = sorted(st.session_state['history'][s_active].keys(),
                      key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)

    for jk in sorted_j:
        d = st.session_state['history'][s_active][jk]
        res_j = d.get("res", [])
        cal_j = d.get("cal", [])
        nb_res = len(res_j)
        nb_cal = len(cal_j)

        # Résumé rapide dans le titre de l'expander
        label_exp = f"📅 {jk}"
        if nb_res > 0:
            label_exp += f"  ·  ✅ {nb_res} résultats"
        elif nb_cal > 0:
            label_exp += f"  ·  📋 {nb_cal} matchs calendrier"
        else:
            label_exp += "  ·  ⚪ Vide"

        with st.expander(label_exp):
            htabs = st.tabs(["📋 Calendrier & Cotes", "🎯 Pronos", "⚽ Résultats", "🏆 Classement"])

            # ── Calendrier ──
            with htabs[0]:
                cal_data = d.get("cal", [])
                if cal_data:
                    rows = []
                    for m in cal_data:
                        o = m.get('o', ['-','-','-'])
                        rows.append({
                            "Domicile": m.get('h','?'),
                            "Extérieur": m.get('a','?'),
                            "Cote 1": o[0] if len(o)>0 else '-',
                            "Cote X": o[1] if len(o)>1 else '-',
                            "Cote 2": o[2] if len(o)>2 else '-',
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.info("Aucun calendrier enregistré pour cette journée.")

            # ── Pronos ──
            with htabs[1]:
                pro_data = d.get("pro", [])
                if pro_data:
                    rows = []
                    for p in pro_data:
                        rows.append({
                            "Match": p.get('m','?'),
                            "Classe": p.get('classe','?'),
                            "Score prédit": p.get('score','?'),
                            "Confiance": f"{p.get('indice','?')}%",
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.info("Aucun pronostic enregistré.")

            # ── Résultats ──
            with htabs[2]:
                if res_j:
                    rows = []
                    for r in res_j:
                        rows.append({
                            "Domicile": r.get('h','?'),
                            "Score": r.get('s','?'),
                            "Extérieur": r.get('a','?'),
                            "Mi-temps": r.get('mt',''),
                            "Buteurs Dom.": r.get('hm',''),
                            "Buteurs Ext.": r.get('am',''),
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.info("Aucun résultat enregistré pour cette journée.")

            # ── Classement après cette journée ──
            with htabs[3]:
                # Recalculer le classement en ne prenant que les journées jusqu'à jk
                j_num_courant = int(re.search(r'\d+', jk).group()) if re.search(r'\d+', jk) else 0
                history_jusque_jk = {}
                for jj in sorted_j:
                    jj_num = int(re.search(r'\d+', jj).group()) if re.search(r'\d+', jj) else 0
                    if jj_num <= j_num_courant:
                        history_jusque_jk[jj] = st.session_state['history'][s_active][jj]

                standings_jk = get_standings(history_jusque_jk, engine.teams_list)

                if not standings_jk.empty and standings_jk['MJ'].sum() > 0:
                    # Colorer selon rang
                    def style_hist(row):
                        rang = row['Rang']
                        if rang <= 4:
                            return ['background-color: rgba(0,255,0,0.12)'] * len(row)
                        elif rang <= 6:
                            return ['background-color: rgba(127,255,212,0.10)'] * len(row)
                        elif rang >= 18:
                            return ['background-color: rgba(255,75,75,0.10)'] * len(row)
                        return [''] * len(row)

                    st.markdown(f"**Classement après {jk}** *(équipes ayant joué uniquement)*")
                    actives = standings_jk[standings_jk['MJ'] > 0]
                    st.dataframe(
                        actives.style.apply(style_hist, axis=1),
                        use_container_width=True,
                        hide_index=True
                    )

                    # Mini-stats journée
                    if res_j:
                        buts_total = 0
                        nb_1 = nb_x = nb_2 = 0
                        for r in res_j:
                            try:
                                sh, sa = map(int, r['s'].replace('-',':').split(':'))
                                buts_total += sh + sa
                                if sh > sa: nb_1 += 1
                                elif sh == sa: nb_x += 1
                                else: nb_2 += 1
                            except: pass

                        st.markdown("---")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("⚽ Buts", buts_total)
                        c2.metric("🏠 Dom. gagne", nb_1)
                        c3.metric("🤝 Nul", nb_x)
                        c4.metric("✈️ Ext. gagne", nb_2)
                else:
                    st.info("Pas encore de résultats pour calculer le classement.")

            # ── BOUTON PRÉDIRE (test rapide du moteur) ──
            st.markdown("---")
            cal_disponible = d.get("cal", [])
            if cal_disponible:
                if st.button(f"🔮 Prédire cette journée (test moteur)", key=f"btn_predire_{jk}"):
                    st.markdown(f"##### 🧪 Résultats de prédiction — {jk}")
                    standings_test = get_standings(st.session_state['history'][s_active], engine.teams_list)

                    # Historique partiel : tout ce qui précède cette journée
                    j_num_test = int(re.search(r'\d+', jk).group()) if re.search(r'\d+', jk) else 0
                    history_avant = {
                        jj: st.session_state['history'][s_active][jj]
                        for jj in sorted_j
                        if (int(re.search(r'\d+', jj).group()) if re.search(r'\d+', jj) else 0) < j_num_test
                    }

                    rows_pred = []
                    for m_test in cal_disponible:
                        r_d = int(standings_test[standings_test['Équipe'] == m_test['h']]['Rang'].values[0]) \
                              if not standings_test[standings_test['Équipe'] == m_test['h']].empty else 10
                        r_e = int(standings_test[standings_test['Équipe'] == m_test['a']]['Rang'].values[0]) \
                              if not standings_test[standings_test['Équipe'] == m_test['a']].empty else 10
                        f_d = get_forme_equipe(st.session_state['history'], s_active, m_test['h'])
                        f_e = get_forme_equipe(st.session_state['history'], s_active, m_test['a'])
                        s_d = get_serie_victoires(f_d)
                        s_e = get_serie_victoires(f_e)

                        pred_test = None
                        if oracle_brain:
                            pred_test = oracle_brain.analyser_match(
                                equipe_dom=m_test['h'], equipe_ext=m_test['a'],
                                cotes=m_test.get('o', [2.0, 3.0, 2.0]),
                                journee=j_num_test, rang_dom=r_d, rang_ext=r_e,
                                serie_dom=s_d, serie_ext=s_e,
                                forme_dom=f_d, forme_ext=f_e
                            )

                        score_reel = None
                        for r_match in d.get("res", []):
                            if r_match.get('h') == m_test['h'] and r_match.get('a') == m_test['a']:
                                score_reel = r_match.get('s', '?')
                                break

                        row = {
                            "Match": f"{m_test['h']} vs {m_test['a']}",
                            "Score prédit": pred_test['score_predit'] if pred_test else "?",
                            "Confiance": pred_test['confiance'] if pred_test else "?",
                            "Choix": pred_test['choix_expert'] if pred_test else "?",
                            "Score réel": score_reel or "–",
                        }
                        if pred_test and score_reel and score_reel != '?':
                            try:
                                sp = pred_test['score_predit']
                                exact = sp.replace(':', '-') == score_reel.replace(':', '-')
                                sh_r, sa_r = map(int, score_reel.replace('-',':').split(':'))
                                sh_p, sa_p = map(int, sp.split(':'))
                                tend_ok = (
                                    (sh_r > sa_r and sh_p > sa_p) or
                                    (sh_r == sa_r and sh_p == sa_p) or
                                    (sh_r < sa_r and sh_p < sa_p)
                                )
                                row["Résultat"] = "✅ Exact" if exact else ("🟡 1N2 OK" if tend_ok else "❌")
                            except:
                                row["Résultat"] = "?"
                        else:
                            row["Résultat"] = "–"
                        rows_pred.append(row)

                    if rows_pred:
                        df_pred = pd.DataFrame(rows_pred)
                        # Colorier selon résultat
                        def style_pred(row):
                            r = row.get("Résultat", "")
                            if "Exact" in str(r):   return ['background-color: rgba(0,255,0,0.15)'] * len(row)
                            if "1N2" in str(r):      return ['background-color: rgba(255,165,0,0.12)'] * len(row)
                            if "❌" in str(r):        return ['background-color: rgba(255,75,75,0.12)'] * len(row)
                            return [''] * len(row)
                        st.dataframe(df_pred.style.apply(style_pred, axis=1),
                                     use_container_width=True, hide_index=True)

                        # Score global du test
                        exacts = sum(1 for r in rows_pred if "Exact" in str(r.get("Résultat", "")))
                        ok_1n2 = sum(1 for r in rows_pred if "1N2" in str(r.get("Résultat", "")))
                        total_t = sum(1 for r in rows_pred if r.get("Résultat", "–") != "–")
                        if total_t > 0:
                            c1t, c2t, c3t = st.columns(3)
                            c1t.metric("✅ Scores exacts", exacts)
                            c2t.metric("🟡 1N2 corrects", ok_1n2)
                            c3t.metric("📊 Taux", f"{(exacts + ok_1n2) / total_t * 100:.0f}%")
            else:
                st.info("Aucun calendrier disponible pour prédire cette journée.")

# ===================== TAB 5 : GESTION =====================
with tabs[5]:
    st.markdown("### ⚙️ Gestion")

    # ── 1) CRÉER UNE NOUVELLE SAISON ──
    st.markdown("#### ➕ Nouvelle Saison")
    ns = st.text_input("Nom (ex: Saison 2027)", key="input_nouvelle_saison")
    if st.button("Créer Saison", key="btn_creer_saison"):
        if ns and ns not in st.session_state['history']:
            st.session_state['history'][ns] = {}
            save_db(st.session_state['history'])
            st.rerun()
        elif ns in st.session_state['history']:
            st.warning("Cette saison existe déjà.")

    st.divider()

    # ── 2) RENOMMER LA SAISON EN COURS ──
    st.markdown("#### ✏️ Renommer la Saison en cours")
    col_rn1, col_rn2 = st.columns([3, 1])
    with col_rn1:
        nouveau_nom = st.text_input(
            f"Nouveau nom pour « {s_active} »",
            value=s_active,
            key="input_renommer_saison"
        )
    with col_rn2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✅ Renommer", key="btn_renommer_saison", use_container_width=True):
            if nouveau_nom and nouveau_nom != s_active:
                if nouveau_nom in st.session_state['history']:
                    st.error("Ce nom est déjà utilisé par une autre saison.")
                else:
                    # Copier les données sous le nouveau nom, supprimer l'ancien
                    st.session_state['history'][nouveau_nom] = st.session_state['history'].pop(s_active)
                    save_db(st.session_state['history'])
                    st.success(f"Saison renommée en « {nouveau_nom} »")
                    st.rerun()

    st.divider()

    # ── 3) EXPORTER BACKUP ──
    st.markdown("#### 📥 Exporter")
    st.download_button(
        label="📥 Télécharger Backup JSON",
        data=json.dumps(st.session_state['history'], indent=4, ensure_ascii=False),
        file_name="oracle_backup.json",
        mime="application/json",
        key="btn_export_backup"
    )

    st.divider()

    # ── 4) IMPORTER & FUSIONNER DES DONNÉES ──
    st.markdown("#### 📤 Importer & Fusionner des Données")
    st.caption("Importez un fichier JSON exporté depuis Oracle. Les données seront **fusionnées** avec l'existant (aucune perte).")

    fichier_import = st.file_uploader(
        "Choisir un fichier backup JSON",
        type=["json"],
        key="uploader_import_backup"
    )

    if fichier_import is not None:
        try:
            contenu_import = json.loads(fichier_import.read().decode("utf-8"))
            
            # Aperçu de ce qui va être importé
            st.markdown("**Aperçu du fichier :**")
            for saison_imp, data_imp in contenu_import.items():
                nb_j = len(data_imp)
                nb_res = sum(len(jd.get("res", [])) for jd in data_imp.values())
                nb_cal = sum(len(jd.get("cal", [])) for jd in data_imp.values())
                exist = "✅ existe déjà" if saison_imp in st.session_state['history'] else "🆕 nouvelle"
                st.markdown(f"- **{saison_imp}** ({exist}) — {nb_j} journées · {nb_cal} matchs calendrier · {nb_res} résultats")

            col_imp1, col_imp2 = st.columns(2)
            with col_imp1:
                if st.button("🔀 Fusionner (recommandé)", key="btn_fusionner", use_container_width=True):
                    nb_saisons_ajoutees = 0
                    nb_journees_fusionnees = 0
                    for saison_imp, data_imp in contenu_import.items():
                        if saison_imp not in st.session_state['history']:
                            st.session_state['history'][saison_imp] = {}
                            nb_saisons_ajoutees += 1
                        for jk_imp, jdata_imp in data_imp.items():
                            if jk_imp not in st.session_state['history'][saison_imp]:
                                # Journée absente : on l'ajoute entièrement
                                st.session_state['history'][saison_imp][jk_imp] = jdata_imp
                                nb_journees_fusionnees += 1
                            else:
                                # Journée existante : fusionner chaque sous-clé
                                existing = st.session_state['history'][saison_imp][jk_imp]
                                for cle in ["cal", "res", "pro"]:
                                    if cle in jdata_imp and not existing.get(cle):
                                        existing[cle] = jdata_imp[cle]
                                nb_journees_fusionnees += 1
                    save_db(st.session_state['history'])
                    # Recharger l'apprentissage IA avec le nouvel historique
                    st.session_state['_ia_history_loaded'] = False
                    st.success(f"✅ Fusion réussie ! {nb_saisons_ajoutees} nouvelles saisons, {nb_journees_fusionnees} journées traitées.")
                    st.rerun()

            with col_imp2:
                if st.button("♻️ Remplacer tout", key="btn_remplacer", use_container_width=True):
                    st.session_state['history'] = contenu_import
                    save_db(st.session_state['history'])
                    st.session_state['_ia_history_loaded'] = False
                    st.warning("⚠️ Remplacement effectué. Toutes les données précédentes ont été remplacées.")
                    st.rerun()

        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier : {e}")

    st.divider()

    # ── 5) ANALYSE CROSS-SAISONS ──
    if oracle_brain and len(st.session_state['history']) >= 2:
        st.markdown("#### 🔄 Apprentissage Cross-Saisons")
        st.caption("Analyse les trajectoires d'équipes à travers toutes les saisons disponibles.")
        if st.button("🧠 Lancer l'analyse cross-saisons", key="btn_cross_saisons"):
            result = oracle_brain.apprendre_cross_saisons(st.session_state['history'])
            st.metric("Équipes analysées", result.get("nb_equipes_analysees", 0))
            st.metric("Saisons parcourues", result.get("nb_saisons", 0))
            rapport_cs = result.get("rapport", "")
            if rapport_cs:
                st.markdown("**Trajectoires détectées :**")
                st.code(rapport_cs)
            mem = result.get("memoire", {})
            if mem:
                rows_mem = [{"Équipe": eq, "Tendance pts/match": v["tendance"],
                             "Saisons": v["nb_saisons"]} for eq, v in mem.items()]
                st.dataframe(pd.DataFrame(rows_mem).sort_values("Tendance pts/match", ascending=False),
                             use_container_width=True, hide_index=True)

# ===================== TAB 6 : PERFORMANCE =====================
with tabs[6]:
    st.markdown("### 📊 Performance Oracle")
    
    # ── Statistiques calculées directement depuis l'historique ──
    history_saison = st.session_state['history'][s_active]
    
    total_matchs_hist = 0
    total_victoires_dom = 0
    total_nuls = 0
    total_victoires_ext = 0
    total_pronos_corrects = 0
    total_pronos = 0
    
    for jk, jdata in history_saison.items():
        res = jdata.get("res", [])
        pro = jdata.get("pro", [])
        cal = jdata.get("cal", [])
        
        for r in res:
            try:
                sh, sa = map(int, r['s'].replace('-', ':').split(':'))
                total_matchs_hist += 1
                if sh > sa: total_victoires_dom += 1
                elif sh == sa: total_nuls += 1
                else: total_victoires_ext += 1
            except: continue
        
        for i, p in enumerate(pro):
            if i < len(res):
                try:
                    sh, sa = map(int, res[i]['s'].replace('-', ':').split(':'))
                    res_reel = "1" if sh > sa else ("X" if sh == sa else "2")
                    # ✅ FIX: la clé est 'prediction' (pas 'p') depuis V52
                    pred_stored = p.get('prediction') or p.get('p')
                    if pred_stored == res_reel:
                        total_pronos_corrects += 1
                    total_pronos += 1
                except: continue
    
    if total_matchs_hist > 0:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Matchs joués", total_matchs_hist)
        c2.metric("Victoires Dom", f"{total_victoires_dom} ({total_victoires_dom/total_matchs_hist*100:.0f}%)")
        c3.metric("Nuls", f"{total_nuls} ({total_nuls/total_matchs_hist*100:.0f}%)")
        c4.metric("Victoires Ext", f"{total_victoires_ext} ({total_victoires_ext/total_matchs_hist*100:.0f}%)")
        
        if total_pronos > 0:
            taux = total_pronos_corrects / total_pronos * 100
            st.markdown(f"### 🎯 Précision des pronos : **{taux:.1f}%** ({total_pronos_corrects}/{total_pronos})")
            color = "green" if taux >= 60 else "orange" if taux >= 45 else "red"
            st.progress(int(taux))
        
        # Détail par équipe
        st.divider()
        st.markdown("#### 📈 Statistiques par Équipe")
        standings_full = get_standings(history_saison, engine.teams_list)
        if not standings_full.empty:
            st.dataframe(standings_full, use_container_width=True, hide_index=True)
        
        # Détail par journée
        st.divider()
        st.markdown("#### 📅 Récapitulatif par Journée")
        jours_data = []
        for jk in sorted(history_saison.keys(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0):
            jdata = history_saison[jk]
            res = jdata.get("res", [])
            cal = jdata.get("cal", [])
            pro = jdata.get("pro", [])
            nb_res = len(res)
            nb_pronos = len(pro)
            jours_data.append({
                "Journée": jk,
                "Matchs joués": nb_res,
                "Pronos": nb_pronos,
                "Calendrier": "✅" if cal else "❌"
            })
        if jours_data:
            st.dataframe(pd.DataFrame(jours_data), use_container_width=True, hide_index=True)
    else:
        if oracle_brain:
            stats = oracle_brain.calculer_performance_globale(history_saison)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Matchs analysés", stats.get("total_matchs", 0))
            c2.metric("Taux 1N2", f"{stats.get('taux_1n2', 0):.1f}%")
            c3.metric("Scores Exacts", stats.get("scores_exacts", 0))
            c4.metric("Points/Match", f"{stats.get('moyenne_points', 0):.2f}")
        else:
            st.info("Aucun résultat enregistré pour cette saison. Commencez par importer un calendrier et des résultats !")

    # Stats IA Apprentissage V2.3 — AFFICHAGE COMPLET
    if IA_DISPONIBLE and moteur_apprentissage is not None:
        st.divider()
        st.markdown("### 🧠 Performance IA Apprentissage")
        stats_ia = moteur_apprentissage.get_stats_apprentissage()
        _mc1, _mc2, _mc3, _mc4 = st.columns(4)
        # Afficher le nb de matchs RÉELS (depuis l'historique) plutôt que le compteur interne
        # qui peut être gonflé par des rechargements multiples
        _matchs_reels_ia = sum(len(jd.get("res",[])) for sd in st.session_state['history'].values() for jd in sd.values())
        _mc1.metric("Matchs appris", _matchs_reels_ia)
        _mc2.metric("Taux réussite IA", f"{stats_ia.get('taux_reussite', 0):.1f}%")
        _mc3.metric("Taux 1N2", f"{stats_ia.get('taux_1n2', 0):.1f}%")
        _mc4.metric("Patterns découverts", stats_ia.get("patterns_connus", 0))

        # ── Patterns Cotes ──
        st.divider()
        st.markdown("#### 📊 Patterns de Cotes")
        if hasattr(moteur_apprentissage, 'patterns') and moteur_apprentissage.patterns:
            _pat_data = []
            for _p, _d in moteur_apprentissage.patterns.items():
                if isinstance(_d, dict) and "total" in _d and _d["total"] >= 1:
                    _tot = _d["total"]
                    _pat_data.append({
                        "Pattern Cotes": _p,
                        "Occurrences": _tot,
                        "Vic. Dom (1)": f"{_d.get('1',0)} ({_d.get('1',0)/_tot*100:.0f}%)",
                        "Nul (X)":      f"{_d.get('X',0)} ({_d.get('X',0)/_tot*100:.0f}%)",
                        "Vic. Ext (2)": f"{_d.get('2',0)} ({_d.get('2',0)/_tot*100:.0f}%)"
                    })
            if _pat_data:
                _df_pat = pd.DataFrame(_pat_data).sort_values("Occurrences", ascending=False)
                st.dataframe(_df_pat, use_container_width=True, hide_index=True)
            else:
                st.info("Enregistrez des résultats pour voir les patterns de cotes !")
        else:
            st.info("Aucun pattern de cotes encore. Enregistrez des résultats.")

        # ── Patterns Classement / Équipes ──
        st.divider()
        st.markdown("#### 🏆 Patterns Classement & Équipes")
        # ✅ FIX: V53 stocke tout dans self.patterns — on filtre les clés classement
        _pat_all = moteur_apprentissage.patterns if hasattr(moteur_apprentissage, 'patterns') else {}
        # Clés classement: contiennent "Z" (zone) ou "dom_" ou "ext_" ou équipe connue
        _KEYS_CATEGORIE = ("COTES_SERREES", "FAVORI_FORT", "FAVORI_MODERE", "MATCH_OUVERT")
        _pat_classement_raw = {k: v for k, v in _pat_all.items()
                               if isinstance(v, dict) and "total" in v
                               and k not in _KEYS_CATEGORIE
                               and not re.match(r'^\d', k)   # pas les cotes fines ex "2.0_3.5_3.5"
                               }
        # Aussi vérifier patterns_classement si attribut séparé existe
        if hasattr(moteur_apprentissage, 'patterns_classement') and moteur_apprentissage.patterns_classement:
            _pat_classement_raw.update(moteur_apprentissage.patterns_classement)

        if _pat_classement_raw:
            _pcl_data = []
            for _pk, _pd in _pat_classement_raw.items():
                if isinstance(_pd, dict) and _pd.get("total", 0) >= 1:
                    _t = _pd["total"]
                    _pcl_data.append({
                        "Pattern": _pk, "Occ.": _t,
                        "1": f"{_pd.get('1',0)} ({_pd.get('1',0)/_t*100:.0f}%)",
                        "X": f"{_pd.get('X',0)} ({_pd.get('X',0)/_t*100:.0f}%)",
                        "2": f"{_pd.get('2',0)} ({_pd.get('2',0)/_t*100:.0f}%)"
                    })
            if _pcl_data:
                st.dataframe(pd.DataFrame(_pcl_data).sort_values("Occ.", ascending=False),
                             use_container_width=True, hide_index=True)
            else:
                st.info("Enregistrez des résultats pour voir les patterns classement.")
        else:
            st.info("Pas encore de patterns classement & équipes. Enregistrez des résultats.")

        # ── Patterns Équipes (domicile/extérieur) ──
        _pat_equipes_raw = {}
        if hasattr(moteur_apprentissage, 'patterns_equipes') and moteur_apprentissage.patterns_equipes:
            _pat_equipes_raw = moteur_apprentissage.patterns_equipes
        else:
            # Chercher les patterns équipes dans self.patterns (clés = noms d'équipes)
            _equipes_set = set(engine.teams_list)
            for _k, _v in _pat_all.items():
                if _k in _equipes_set and isinstance(_v, dict):
                    _pat_equipes_raw[_k] = _v

        if _pat_equipes_raw:
            st.divider()
            st.markdown("#### ⚽ Statistiques par Équipe (appris)")
            _peq_data = []
            for _eq, _ed in _pat_equipes_raw.items():
                if isinstance(_ed, dict):
                    # Format V53 : {'domicile': {V,N,D,total}, 'exterieur': {V,N,D,total}}
                    if "domicile" in _ed:
                        _dom = _ed.get("domicile", {}); _ext = _ed.get("exterieur", {})
                        _td = _dom.get("total", 0); _te = _ext.get("total", 0); _tt = _td + _te
                        if _tt >= 1:
                            _peq_data.append({
                                "Équipe": _eq, "Matchs": _tt,
                                "V Dom": f"{_dom.get('V',0)}/{_td}" if _td else "–",
                                "V Ext": f"{_ext.get('V',0)}/{_te}" if _te else "–",
                            })
                    elif _ed.get("total", 0) >= 1:
                        _t = _ed["total"]
                        _peq_data.append({
                            "Équipe": _eq, "Matchs": _t,
                            "Victoires": f"{_ed.get('V',0)} ({_ed.get('V',0)/_t*100:.0f}%)",
                            "Nuls":      f"{_ed.get('N',0)} ({_ed.get('N',0)/_t*100:.0f}%)",
                            "Défaites":  f"{_ed.get('D',0)} ({_ed.get('D',0)/_t*100:.0f}%)"
                        })
            if _peq_data:
                st.dataframe(pd.DataFrame(_peq_data).sort_values("Matchs", ascending=False),
                             use_container_width=True, hide_index=True)

        # ── Rapport complet si disponible ──
        if hasattr(moteur_apprentissage, 'generer_rapport_patterns'):
            st.divider()
            if st.button("📋 Générer rapport complet patterns V2.3", key="btn_rapport_v52"):
                _rp = moteur_apprentissage.generer_rapport_patterns()
                st.code(_rp, language=None)

# ===================== TAB 7 : ASSISTANT IA — CHAT MESSENGER =====================
import streamlit.components.v1 as components
import datetime as _dt

with tabs[7]:

    # ══════════════════════════════════════════════════════
    # INIT session state
    # ══════════════════════════════════════════════════════
    if "chat_messages" not in st.session_state:
        st.session_state['chat_messages'] = load_chat_history()
    if 'active_chat_session' not in st.session_state:
        st.session_state['active_chat_session'] = None
    if 'chat_theme' not in st.session_state:
        st.session_state['chat_theme'] = "🟢 Vert Oracle"

    # ══════════════════════════════════════════════════════
    # APPEL IA
    # ══════════════════════════════════════════════════════
    def _call_ia(user_q: str):
        try:
            # ── PRIORITÉ 1 : Clé Groq directe (session state) ──
            # On vérifie d'abord la clé directe car moteur_ia_chat peut être
            # importé sans avoir la clé API configurée, ce qui donne "Mode Offline"
            _gk = st.session_state.get('groq_api_key_direct', '')
            # Injecter aussi la clé depuis moteur_ia_chat si disponible
            if not _gk and CHAT_IA_DISPONIBLE and moteur_ia_chat is not None:
                _gk = getattr(moteur_ia_chat, 'api_key', '') or ''
            if _gk:
                from groq import Groq as _GQ
                _gc = _GQ(api_key=_gk)
                _std2 = get_standings(st.session_state['history'][s_active], engine.teams_list)
                _ctx2 = build_full_context(st.session_state['history'], s_active, _std2, next_j)
                _r = _gc.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role":"system","content":f"Tu es Oracle Mahita IA, assistant pronostics football expert. "
                         f"Réponds en français, de façon précise et détaillée.\n\nCONTEXTE SAISON COMPLÈTE:\n{_ctx2}"},
                        {"role":"user","content":user_q}
                    ],
                    max_tokens=800, temperature=0.7
                )
                return {"texte": _r.choices[0].message.content, "source": "groq"}
            # ── PRIORITÉ 2 : moteur_ia_chat (si connecté via son propre client) ──
            if CHAT_IA_DISPONIBLE and moteur_ia_chat is not None:
                _est_conn = getattr(moteur_ia_chat, 'est_connecte', lambda: False)()
                if _est_conn:
                    _std = get_standings(st.session_state['history'][s_active], engine.teams_list)
                    _ctx = build_full_context(st.session_state['history'], s_active, _std, next_j)
                    if hasattr(moteur_ia_chat, 'set_contexte'):
                        moteur_ia_chat.set_contexte(
                            history=st.session_state['history'],
                            saison_active=s_active,
                            standings=_std,
                            prochaine_journee=next_j,
                            contexte_complet=_ctx
                        )
                    return moteur_ia_chat.discuter(user_q)
            # ── OFFLINE : aucune clé disponible ──
            return {"texte": "💡 Saisissez votre clé Groq API dans la section **Configuration Groq** ci-dessous pour activer l'IA.", "source": "offline"}
        except Exception as _ex:
            return {"texte": f"Erreur connexion Groq : {_ex}", "source": "offline"}

    # ══════════════════════════════════════════════════════
    # LIRE MESSAGE ENTRANT (query_params — envoyé par le HTML)
    # ══════════════════════════════════════════════════════
    _incoming = None
    try:
        _qraw = st.query_params.get("_ochat", None)
        if _qraw:
            # Streamlit décode automatiquement l'URL — pas besoin de décoder manuellement
            _incoming = _qraw if isinstance(_qraw, str) else str(_qraw)
            # Supprimer proprement le paramètre
            _new_params = {k: v for k, v in st.query_params.items() if k != "_ochat"}
            st.query_params.clear()
            for k, v in _new_params.items():
                st.query_params[k] = v
    except Exception:
        pass

    if not _incoming and st.session_state.get('_pending_chat_input'):
        _incoming = st.session_state.pop('_pending_chat_input')

    # Obtenir la session active
    _sid = get_or_create_active_session()
    # Synchroniser chat_messages avec la session active
    if st.session_state.get('_last_loaded_session') != _sid:
        st.session_state['chat_messages'] = load_session_messages(_sid)
        st.session_state['_last_loaded_session'] = _sid

    # Traiter le message entrant
    if _incoming:
        _already = [m.get("content","") for m in st.session_state.get('chat_messages',[])[-3:] if m.get("role")=="user"]
        if _incoming not in _already:
            _ts = _dt.datetime.now().isoformat()
            st.session_state.chat_messages.append({"role":"user","content":_incoming,"ts":_ts})
            with st.spinner("🔮 Oracle réfléchit..."):
                _rep = _call_ia(_incoming)
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": _rep.get("texte", "Pas de réponse."),
                "source": _rep.get("source", "offline"),
                "ts": _dt.datetime.now().isoformat()
            })
            save_session_messages(_sid, st.session_state.chat_messages)
            save_chat_history(st.session_state.chat_messages)
            st.rerun()

    # ══════════════════════════════════════════════════════
    # THÈMES
    # ══════════════════════════════════════════════════════
    _THEMES = {
        "🟢 Vert Oracle": {
            "hd": "linear-gradient(135deg,#00FF88,#7FFFD4)",
            "hd_txt": "#002211", "hd_sub": "#003322", "dot": "#006644",
            "msgs_bg": "#071410", "scroll": "#00FF88",
            "wel_bg": "rgba(0,255,136,.07)", "wel_bd": "rgba(0,255,136,.2)", "wel_c": "#7FFFD4",
            "bu_u": "linear-gradient(135deg,#00FF88,#00e07a)", "bu_u_c": "#001a0d", "bu_u_sh": "rgba(0,255,136,.4)",
            "av": "linear-gradient(135deg,#7FFFD4,#00FF88)",
            "bu_b_bg": "rgba(255,255,255,.07)", "bu_b_bd": "rgba(127,255,212,.2)", "bu_b_c": "#ffffff",
            "lbl": "#00FF88", "typ": "#7FFFD4",
            "bar_bg": "#0a1e16", "bar_bd": "rgba(0,255,136,.15)",
            "inp_bg": "rgba(255,255,255,.06)", "inp_bd": "rgba(0,255,136,.25)",
            "inp_foc": "#00FF88", "inp_fsh": "rgba(0,255,136,.1)", "inp_ph": "rgba(127,255,212,.4)",
            "snd": "linear-gradient(135deg,#00FF88,#7FFFD4)", "snd_c": "#001a0d", "snd_sh": "rgba(0,255,136,.5)",
            "root_sh": "rgba(0,255,140,.2)", "root_bd": "rgba(0,255,140,.3)",
        },
        "🔵 Bleu Professionnel": {
            "hd": "linear-gradient(135deg,#1a73e8,#4fc3f7)",
            "hd_txt": "#ffffff", "hd_sub": "#cce4ff", "dot": "#81d4fa",
            "msgs_bg": "#0d1b2a", "scroll": "#1a73e8",
            "wel_bg": "rgba(26,115,232,.08)", "wel_bd": "rgba(26,115,232,.25)", "wel_c": "#4fc3f7",
            "bu_u": "linear-gradient(135deg,#1a73e8,#1565c0)", "bu_u_c": "#ffffff", "bu_u_sh": "rgba(26,115,232,.4)",
            "av": "linear-gradient(135deg,#4fc3f7,#1a73e8)",
            "bu_b_bg": "rgba(255,255,255,.06)", "bu_b_bd": "rgba(79,195,247,.2)", "bu_b_c": "#e8f4fd",
            "lbl": "#4fc3f7", "typ": "#4fc3f7",
            "bar_bg": "#0a1929", "bar_bd": "rgba(26,115,232,.2)",
            "inp_bg": "rgba(255,255,255,.05)", "inp_bd": "rgba(26,115,232,.3)",
            "inp_foc": "#4fc3f7", "inp_fsh": "rgba(79,195,247,.15)", "inp_ph": "rgba(79,195,247,.4)",
            "snd": "linear-gradient(135deg,#1a73e8,#4fc3f7)", "snd_c": "#ffffff", "snd_sh": "rgba(26,115,232,.5)",
            "root_sh": "rgba(26,115,232,.2)", "root_bd": "rgba(26,115,232,.35)",
        },
        "🟣 Violet Premium": {
            "hd": "linear-gradient(135deg,#7c3aed,#c084fc)",
            "hd_txt": "#ffffff", "hd_sub": "#ede9fe", "dot": "#a78bfa",
            "msgs_bg": "#0f0a1e", "scroll": "#7c3aed",
            "wel_bg": "rgba(124,58,237,.08)", "wel_bd": "rgba(124,58,237,.25)", "wel_c": "#c084fc",
            "bu_u": "linear-gradient(135deg,#7c3aed,#6d28d9)", "bu_u_c": "#ffffff", "bu_u_sh": "rgba(124,58,237,.4)",
            "av": "linear-gradient(135deg,#c084fc,#7c3aed)",
            "bu_b_bg": "rgba(255,255,255,.06)", "bu_b_bd": "rgba(192,132,252,.2)", "bu_b_c": "#f3e8ff",
            "lbl": "#c084fc", "typ": "#c084fc",
            "bar_bg": "#0c0818", "bar_bd": "rgba(124,58,237,.2)",
            "inp_bg": "rgba(255,255,255,.05)", "inp_bd": "rgba(124,58,237,.3)",
            "inp_foc": "#c084fc", "inp_fsh": "rgba(192,132,252,.15)", "inp_ph": "rgba(192,132,252,.4)",
            "snd": "linear-gradient(135deg,#7c3aed,#c084fc)", "snd_c": "#ffffff", "snd_sh": "rgba(124,58,237,.5)",
            "root_sh": "rgba(124,58,237,.2)", "root_bd": "rgba(124,58,237,.35)",
        },
        "🟠 Orange Sport": {
            "hd": "linear-gradient(135deg,#f97316,#fbbf24)",
            "hd_txt": "#1a0a00", "hd_sub": "#431407", "dot": "#92400e",
            "msgs_bg": "#1a0e00", "scroll": "#f97316",
            "wel_bg": "rgba(249,115,22,.08)", "wel_bd": "rgba(249,115,22,.25)", "wel_c": "#fbbf24",
            "bu_u": "linear-gradient(135deg,#f97316,#ea580c)", "bu_u_c": "#ffffff", "bu_u_sh": "rgba(249,115,22,.4)",
            "av": "linear-gradient(135deg,#fbbf24,#f97316)",
            "bu_b_bg": "rgba(255,255,255,.06)", "bu_b_bd": "rgba(251,191,36,.2)", "bu_b_c": "#fff7ed",
            "lbl": "#fbbf24", "typ": "#fbbf24",
            "bar_bg": "#150b00", "bar_bd": "rgba(249,115,22,.2)",
            "inp_bg": "rgba(255,255,255,.05)", "inp_bd": "rgba(249,115,22,.3)",
            "inp_foc": "#fbbf24", "inp_fsh": "rgba(251,191,36,.15)", "inp_ph": "rgba(251,191,36,.4)",
            "snd": "linear-gradient(135deg,#f97316,#fbbf24)", "snd_c": "#1a0a00", "snd_sh": "rgba(249,115,22,.5)",
            "root_sh": "rgba(249,115,22,.2)", "root_bd": "rgba(249,115,22,.35)",
        },
        "⚪ Blanc Élégant": {
            "hd": "linear-gradient(135deg,#374151,#6b7280)",
            "hd_txt": "#ffffff", "hd_sub": "#d1d5db", "dot": "#9ca3af",
            "msgs_bg": "#f9fafb", "scroll": "#374151",
            "wel_bg": "rgba(55,65,81,.06)", "wel_bd": "rgba(55,65,81,.15)", "wel_c": "#374151",
            "bu_u": "linear-gradient(135deg,#374151,#1f2937)", "bu_u_c": "#ffffff", "bu_u_sh": "rgba(55,65,81,.3)",
            "av": "linear-gradient(135deg,#6b7280,#374151)",
            "bu_b_bg": "#ffffff", "bu_b_bd": "rgba(55,65,81,.15)", "bu_b_c": "#111827",
            "lbl": "#374151", "typ": "#6b7280",
            "bar_bg": "#f3f4f6", "bar_bd": "rgba(55,65,81,.15)",
            "inp_bg": "#ffffff", "inp_bd": "rgba(55,65,81,.2)",
            "inp_foc": "#374151", "inp_fsh": "rgba(55,65,81,.1)", "inp_ph": "rgba(55,65,81,.4)",
            "snd": "linear-gradient(135deg,#374151,#6b7280)", "snd_c": "#ffffff", "snd_sh": "rgba(55,65,81,.3)",
            "root_sh": "rgba(55,65,81,.15)", "root_bd": "rgba(55,65,81,.2)",
        },
    }

    # ══════════════════════════════════════════════════════
    # BARRE DE CONTRÔLE (thème + nouvelle session)
    # ══════════════════════════════════════════════════════
    _ctrl1, _ctrl2, _ctrl3 = st.columns([2, 2, 1])
    with _ctrl1:
        _sel_theme = st.selectbox(
            "🎨 Thème", list(_THEMES.keys()),
            index=list(_THEMES.keys()).index(st.session_state['chat_theme'])
                  if st.session_state['chat_theme'] in _THEMES else 0,
            key="chat_theme_sel_v50", label_visibility="collapsed"
        )
        if _sel_theme != st.session_state['chat_theme']:
            st.session_state['chat_theme'] = _sel_theme
            st.rerun()

    with _ctrl3:
        if st.button("➕ Nouveau chat", key="btn_new_chat_v50", use_container_width=True):
            _new_sid = new_chat_session()
            st.session_state['active_chat_session'] = _new_sid
            st.session_state['chat_messages'] = []
            st.session_state['_last_loaded_session'] = _new_sid
            st.rerun()

    # ══════════════════════════════════════════════════════
    # SÉLECTEUR DE SESSION (panneau latéral intégré)
    # ══════════════════════════════════════════════════════
    _all_sessions = load_chat_sessions()
    if _all_sessions:
        _sorted_sids = sorted(_all_sessions.keys(), reverse=True)
        _session_labels = {
            sid: f"💬 {_all_sessions[sid].get('title','Chat')} — {sid[6:8]}/{sid[4:6]}/{sid[0:4]} {sid[9:11]}:{sid[11:13]}"
            for sid in _sorted_sids
        }
        _current_idx = _sorted_sids.index(_sid) if _sid in _sorted_sids else 0
        _chosen_label = st.selectbox(
            "📂 Historique des chats",
            options=list(_session_labels.values()),
            index=_current_idx,
            key="chat_session_sel_v50"
        )
        # Retrouver le sid depuis le label choisi
        _chosen_sid = next((s for s, l in _session_labels.items() if l == _chosen_label), _sid)
        if _chosen_sid != _sid:
            st.session_state['active_chat_session'] = _chosen_sid
            st.session_state['chat_messages'] = load_session_messages(_chosen_sid)
            st.session_state['_last_loaded_session'] = _chosen_sid
            _sid = _chosen_sid
            st.rerun()

        # Renommer la session courante
        with st.expander("✏️ Renommer ce chat", expanded=False):
            _rename_val = st.text_input("Nouveau titre", value=_all_sessions.get(_sid, {}).get("title", ""), key="rename_input_v50")
            if st.button("💾 Enregistrer le nom", key="btn_rename_v50"):
                _sess = load_chat_sessions()
                if _sid in _sess:
                    _sess[_sid]["title"] = _rename_val
                    _sess[_sid]["_titled"] = True
                    save_chat_sessions(_sess)
                    st.rerun()

    # ══════════════════════════════════════════════════════
    # STATUT CONNEXION IA (V53 FIX: affiché en haut, visible)
    # ══════════════════════════════════════════════════════
    _gk_ok = bool(st.session_state.get('groq_api_key_direct', ''))
    _chat_conn = CHAT_IA_DISPONIBLE and moteur_ia_chat is not None and getattr(moteur_ia_chat, 'est_connecte', lambda: False)()
    _groq_active = _gk_ok or _chat_conn

    if _groq_active:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;padding:10px 16px;
             background:rgba(0,255,136,0.1);border:1px solid #00FF88;border-radius:10px;margin-bottom:10px;">
          <span style="font-size:18px;">🟢</span>
          <div>
            <span style="color:#00FF88;font-weight:700;font-size:14px;">Groq IA Connecté</span>
            <span style="color:#888;font-size:12px;margin-left:10px;">Les réponses utilisent le modèle LLaMA-3.3-70b</span>
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;padding:10px 16px;
             background:rgba(255,165,0,0.1);border:1px solid #FFA500;border-radius:10px;margin-bottom:10px;">
          <span style="font-size:18px;">🟡</span>
          <div>
            <span style="color:#FFA500;font-weight:700;font-size:14px;">Mode Offline</span>
            <span style="color:#888;font-size:12px;margin-left:10px;">Configurez votre clé Groq ci-dessous pour activer l'IA</span>
          </div>
        </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # RENDU CHAT HTML
    # ══════════════════════════════════════════════════════
    _T = _THEMES[st.session_state['chat_theme']]
    _msgs = st.session_state.get('chat_messages', [])
    _msgs_json = json.dumps(_msgs, ensure_ascii=False)

    _CHAT_HTML = f"""<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{height:100%;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:transparent;}}
.root{{display:flex;flex-direction:column;height:500px;border-radius:18px;overflow:hidden;
  box-shadow:0 0 40px {_T['root_sh']},0 8px 32px rgba(0,0,0,.4);
  border:1.5px solid {_T['root_bd']};}}
.hd{{background:{_T['hd']};padding:13px 16px;display:flex;align-items:center;gap:12px;flex-shrink:0;}}
.hd-av{{width:44px;height:44px;border-radius:50%;background:rgba(255,255,255,.3);
  display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0;}}
.hd-name{{color:{_T['hd_txt']};font-weight:800;font-size:15px;}}
.hd-status{{color:{_T['hd_sub']};font-size:11px;margin-top:2px;display:flex;align-items:center;gap:5px;}}
.dot{{width:8px;height:8px;border-radius:50%;background:{_T['dot']};animation:pulse 2s infinite;}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.6;transform:scale(.85)}}}}
.msgs{{flex:1;overflow-y:auto;padding:14px 12px;display:flex;flex-direction:column;gap:10px;
  background:{_T['msgs_bg']};scrollbar-width:thin;scrollbar-color:{_T['scroll']} {_T['msgs_bg']};}}
.msgs::-webkit-scrollbar{{width:4px;}}
.msgs::-webkit-scrollbar-thumb{{background:{_T['scroll']};border-radius:4px;}}
.welcome{{background:{_T['wel_bg']};border:1px solid {_T['wel_bd']};border-radius:14px;
  padding:12px 14px;color:{_T['wel_c']};font-size:13px;text-align:center;}}
.bw-u{{display:flex;justify-content:flex-end;}}
.bu-u{{background:{_T['bu_u']};color:{_T['bu_u_c']};padding:10px 15px;
  border-radius:20px 20px 4px 20px;max-width:78%;font-size:14px;line-height:1.45;
  word-break:break-word;font-weight:600;box-shadow:0 3px 16px {_T['bu_u_sh']};}}
.bu-u .ts{{color:rgba(0,0,0,.3);font-size:10px;margin-top:3px;text-align:right;}}
.bw-b{{display:flex;justify-content:flex-start;align-items:flex-end;gap:8px;}}
.av-b{{width:32px;height:32px;border-radius:50%;background:{_T['av']};
  display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;margin-bottom:2px;}}
.bu-b{{background:{_T['bu_b_bg']};border:1px solid {_T['bu_b_bd']};color:{_T['bu_b_c']};
  padding:10px 15px;border-radius:20px 20px 20px 4px;max-width:82%;font-size:14px;
  line-height:1.5;word-break:break-word;}}
.src-lbl{{font-size:10px;color:{_T['lbl']};font-weight:700;margin-bottom:4px;}}
.bu-b .ts{{font-size:10px;color:rgba(127,200,180,.45);margin-top:4px;}}
.typing{{display:flex;gap:5px;align-items:center;padding:4px 2px;}}
.typing span{{width:9px;height:9px;border-radius:50%;background:{_T['typ']};opacity:.5;animation:bnc 1.1s infinite;}}
.typing span:nth-child(2){{animation-delay:.18s;}}
.typing span:nth-child(3){{animation-delay:.36s;}}
@keyframes bnc{{0%,80%,100%{{transform:scale(.65);opacity:.3}}40%{{transform:scale(1.15);opacity:1}}}}
.bar{{display:none !important;}}
@media(max-width:600px){{.root{{height:420px;}}}}
</style></head><body>
<div class="root">
  <div class="hd">
    <div class="hd-av">🔮</div>
    <div style="flex:1;">
      <div class="hd-name">Oracle Mahita IA</div>
      <div class="hd-status"><span class="dot"></span> En ligne · Assistant pronostics</div>
    </div>
  </div>
  <div class="msgs" id="msgs"></div>
  <div class="bar">
    <textarea class="inp" id="inp" placeholder="Écrivez votre message..." rows="1"></textarea>
    <button class="snd" id="snd">&#10148;</button>
  </div>
</div>
<script>
const MSGS={_msgs_json};
function esc(t){{return String(t||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}}
function fmt(ts){{
  try{{const d=new Date(ts);return d.getHours().toString().padStart(2,'0')+':'+d.getMinutes().toString().padStart(2,'0');}}
  catch(e){{return'';}}
}}
function renderAll(){{
  const box=document.getElementById('msgs');
  let h='<div class="welcome">🔮 Bonjour ! Posez-moi n\\'importe quelle question sur vos pronostics, classements ou résultats.</div>';
  MSGS.forEach(function(m){{
    const t=fmt(m.ts||'');
    if(m.role==='user'){{
      h+='<div class="bw-u"><div class="bu-u">'+esc(m.content).replace(/\\n/g,'<br>')+'<div class="ts">'+t+'</div></div></div>';
    }}else{{
      const src=m.source==='groq'?'🧠 Groq':'🤖 Offline';
      h+='<div class="bw-b"><div class="av-b">🔮</div><div class="bu-b"><div class="src-lbl">'+src+'</div>'
       +esc(m.content).replace(/\\n/g,'<br>')+'<div class="ts">'+t+'</div></div></div>';
    }}
  }});
  box.innerHTML=h;
  box.scrollTop=box.scrollHeight;
}}
const inp=document.getElementById('inp');
inp.addEventListener('input',function(){{this.style.height='auto';this.style.height=Math.min(this.scrollHeight,120)+'px';}});
function doSend(){{
  const snd=document.getElementById('snd');
  const text=inp.value.trim();
  if(!text)return;
  inp.value='';inp.style.height='auto';
  inp.disabled=true;snd.disabled=true;
  const box=document.getElementById('msgs');
  box.innerHTML+='<div class="bw-u"><div class="bu-u">'+esc(text).replace(/\\n/g,'<br>')+'</div></div>';
  box.innerHTML+='<div class="bw-b"><div class="av-b">🔮</div><div class="bu-b"><div class="typing"><span></span><span></span><span></span></div></div></div>';
  box.scrollTop=box.scrollHeight;
  // ✅ FIX : utiliser URLSearchParams directement sur la fenêtre parente sans double-encodage
  try{{
    const url=new URL(window.parent.location.href);
    url.searchParams.set('_ochat', text);
    window.parent.location.href=url.toString();
  }}catch(err){{
    inp.disabled=false;snd.disabled=false;
  }}
}}
inp.addEventListener('keydown',function(e){{if(e.key==='Enter'&&!e.shiftKey){{e.preventDefault();doSend();}}}});
renderAll();
</script></body></html>"""

    components.html(_CHAT_HTML, height=500, scrolling=False)

    st.markdown("---")

    # ══════════════════════════════════════════════════════
    # INPUT NATIF STREAMLIT (V51 design — 100% fiable)
    # ══════════════════════════════════════════════════════
    _chat_native = st.chat_input("💬 Posez votre question à Oracle Mahita IA...")
    if _chat_native and _chat_native.strip():
        st.session_state['_pending_chat_input'] = _chat_native.strip()
        st.rerun()

    # Config Groq — avec statut visible après connexion
    with st.expander("🔑 Configuration Groq API", expanded=not _groq_active):
        _c1, _c2 = st.columns([3,1])
        with _c1:
            _default_key = st.session_state.get('groq_api_key_direct', '')
            if CHAT_IA_DISPONIBLE and moteur_ia_chat is not None:
                _default_key = _default_key or getattr(moteur_ia_chat, 'api_key', '')
            _api_key = st.text_input("Clé API Groq",
                                     value=_default_key,
                                     type="password", placeholder="gsk_xxx...",
                                     key="groq_key_input_v53")
        with _c2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔗 Connecter", use_container_width=True, key="btn_groq_v53"):
                if _api_key:
                    os.environ["GROQ_API_KEY"] = _api_key
                    st.session_state['groq_api_key_direct'] = _api_key
                    if CHAT_IA_DISPONIBLE and moteur_ia_chat is not None:
                        moteur_ia_chat.api_key = _api_key
                        try:
                            from groq import Groq
                            moteur_ia_chat.client = Groq(api_key=_api_key)
                        except: pass
                    try:
                        from groq import Groq as _GT
                        _GT(api_key=_api_key).chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role":"user","content":"ok"}],
                            max_tokens=5
                        )
                        st.success("✅ Groq connecté avec succès ! Rechargez la page pour voir le badge vert.")
                    except Exception as _ge:
                        st.error(f"Erreur connexion : {_ge}")
                    st.rerun()
                else:
                    st.warning("Entrez d'abord votre clé API Groq.")
        _sc1, _sc2, _sc3 = st.columns(3)
        if _groq_active:
            _sc1.success("🟢 Groq actif")
        else:
            _sc1.warning("🟡 Offline")
        _sia2 = moteur_apprentissage.get_stats_apprentissage() if (IA_DISPONIBLE and moteur_apprentissage) else {"total":0}
        _sc2.metric("Matchs appris", _sia2.get("total",0))
        _tr = sum(len(jd.get("res",[])) for sd in st.session_state['history'].values() for jd in sd.values())
        _sc3.metric("Résultats stockés", _tr)
        st.caption("💡 Obtenez votre clé gratuite sur https://console.groq.com")

    # Export + effacer session + supprimer session
    _col1, _col2, _col3 = st.columns(3)
    with _col1:
        if st.button("💾 Exporter chat", use_container_width=True, key="btn_export_v50"):
            _export_data = json.dumps(st.session_state.chat_messages, indent=2, ensure_ascii=False)
            _sess_title = _all_sessions.get(_sid, {}).get("title", "chat")
            st.download_button("📥 Télécharger JSON",
                data=_export_data,
                file_name=f"oracle_{_sess_title[:20].replace(' ','_')}.json",
                mime="application/json")
    with _col2:
        if st.button("🗑️ Effacer ce chat", use_container_width=True, key="btn_clr_v50"):
            st.session_state.chat_messages = []
            save_session_messages(_sid, [])
            save_chat_history([])
            st.rerun()
    with _col3:
        if st.button("❌ Supprimer session", use_container_width=True, key="btn_del_v50"):
            _sess = load_chat_sessions()
            if _sid in _sess:
                del _sess[_sid]
                save_chat_sessions(_sess)
            st.session_state['active_chat_session'] = None
            st.session_state['chat_messages'] = []
            st.session_state['_last_loaded_session'] = None
            st.rerun()

    # Suggestions
    st.markdown("<p style='color:#00FF88;font-size:12px;margin:10px 0 4px 0;'>⚡ Suggestions :</p>", unsafe_allow_html=True)
    _SUGGS = [
        "Quelle équipe est la plus en forme ?",
        "Qui est favori pour le titre ?",
        "Meilleures cotes de la prochaine journée",
        "Analyse les résultats récents",
    ]
    _sg2 = st.columns(2)
    for _si, _sg in enumerate(_SUGGS):
        with _sg2[_si % 2]:
            if st.button(_sg, key=f"sg50_{_si}", use_container_width=True):
                st.session_state['_pending_chat_input'] = _sg
                st.rerun()

# ===================== Sauvegarde Globale =====================
# ===================== Sauvegarde Globale =====================
if st.button("💾 Sauvegarder tout maintenant", key="btn_save_all"):
    save_db(st.session_state['history'])
    if IA_DISPONIBLE:
        moteur_apprentissage.save()
    custom_notify("Historique sauvegardé avec succès !", "#00FF00")
