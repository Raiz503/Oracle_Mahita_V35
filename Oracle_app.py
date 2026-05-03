"""
╔══════════════════════════════════════════════════════════════╗
║           ORACLE MAHITA V36.0 — IA INTÉGRÉE                 ║
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

# ── Import IA ──
try:
    from moteur_apprentissage import moteur_apprentissage
    from moteur_ia_chat import moteur_ia_chat
    IA_DISPONIBLE = True
except ImportError:
    IA_DISPONIBLE = False

# ── Import Cerveau I ──
try:
    from moteur_cerveau1 import cerveau1 as oracle_brain
except ImportError:
    oracle_brain = None

# ── Configuration ──
st.set_page_config(page_title="Oracle Mahita V36", layout="wide", page_icon="🔮")

# ── CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');

.main-header {
    text-align: center; padding: 20px; 
    background: #0E1117; margin-bottom: 20px;
    border-bottom: 3px solid #7FFFD4;
}
.logo-container {
    display: flex; align-items: center; justify-content: center; gap: 20px;
    margin-bottom: 10px;
}
.logo-svg {
    width: 80px; height: 80px;
}
.header-title {
    color: #7FFFD4; font-size: 3em; font-weight: 900; 
    font-family: 'Orbitron', sans-serif;
    text-transform: uppercase; letter-spacing: 4px;
    text-shadow: 0 0 20px #7FFFD4, 0 0 40px rgba(127,255,212,0.5);
}
.header-subtitle {
    color: #888; font-size: 1.1em; letter-spacing: 2px;
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

# ===================== LOGO SVG =====================
LOGO_SVG = """
<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Fond vert d'eau lumineux -->
  <circle cx="100" cy="100" r="95" fill="#7FFFD4" opacity="0.15"/>
  <circle cx="100" cy="100" r="85" fill="none" stroke="#7FFFD4" stroke-width="2" opacity="0.6"/>

  <!-- Boule de cristal extérieure -->
  <circle cx="100" cy="100" r="75" fill="none" stroke="#7FFFD4" stroke-width="3"/>
  <circle cx="100" cy="100" r="70" fill="#0E1117" opacity="0.8"/>

  <!-- Glow effect -->
  <circle cx="100" cy="100" r="72" fill="none" stroke="#7FFFD4" stroke-width="1" opacity="0.3">
    <animate attributeName="r" values="72;75;72" dur="3s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.3;0.6;0.3" dur="3s" repeatCount="indefinite"/>
  </circle>

  <!-- Demi-ballon de foot (gauche) -->
  <path d="M 55 100 A 45 45 0 0 1 145 100" fill="none" stroke="#7FFFD4" stroke-width="2"/>
  <path d="M 70 75 L 85 90 L 70 105" fill="none" stroke="#7FFFD4" stroke-width="1.5"/>
  <path d="M 130 75 L 115 90 L 130 105" fill="none" stroke="#7FFFD4" stroke-width="1.5"/>
  <path d="M 85 90 L 115 90" fill="none" stroke="#7FFFD4" stroke-width="1.5"/>

  <!-- Demi-cerveau IA (droite) -->
  <path d="M 100 55 Q 140 55 140 100 Q 140 145 100 145" fill="none" stroke="#00FF00" stroke-width="2"/>

  <!-- Neurones / connexions -->
  <circle cx="115" cy="80" r="4" fill="#00FF00"/>
  <circle cx="130" cy="95" r="4" fill="#00FF00"/>
  <circle cx="120" cy="115" r="4" fill="#00FF00"/>
  <circle cx="135" cy="125" r="4" fill="#00FF00"/>

  <line x1="115" y1="80" x2="130" y2="95" stroke="#00FF00" stroke-width="1.5"/>
  <line x1="130" y1="95" x2="120" y2="115" stroke="#00FF00" stroke-width="1.5"/>
  <line x1="120" y1="115" x2="135" y2="125" stroke="#00FF00" stroke-width="1.5"/>

  <!-- Étoiles de prédiction -->
  <polygon points="100,25 103,33 111,33 105,38 107,46 100,41 93,46 95,38 89,33 97,33" fill="#FFD700"/>
  <polygon points="45,70 47,75 52,75 48,78 50,83 45,80 40,83 42,78 38,75 43,75" fill="#FFD700" opacity="0.7"/>
  <polygon points="155,70 157,75 162,75 158,78 160,83 155,80 150,83 152,78 148,75 153,75" fill="#FFD700" opacity="0.7"/>

  <!-- Base de la boule de cristal -->
  <ellipse cx="100" cy="175" rx="30" ry="8" fill="none" stroke="#7FFFD4" stroke-width="2"/>
  <path d="M 75 175 Q 100 190 125 175" fill="none" stroke="#7FFFD4" stroke-width="2" opacity="0.5"/>
</svg>
"""

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

if 'history' not in st.session_state:
    st.session_state['history'] = load_db()
    if not st.session_state['history']:
        st.session_state['history']["Saison 2026"] = {}

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

# ===================== OCR CALENDRIER (NOUVEAU) =====================
def ocr_calendrier_bet261(image_bytes, debug=False):
    """OCR avancé pour calendrier Bet261 avec détection boutons verts et correction cotes."""
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
        if 500 < area < 10000 and 1.5 < aspect < 8.0 and bw > 30 and bh > 10:
            boutons.append({
                'x': x, 'y': y, 'w': bw, 'h': bh,
                'cx': x + bw//2, 'cy': y + bh//2,
                'area': area
            })

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

    # Filtrer lignes avec exactement 3 boutons
    lignes_valides = [l for l in lignes if len(l['boutons']) == 3]

    # Ignorer header
    min_y = int(h_img * 0.15)
    lignes_valides = [l for l in lignes_valides if l['cy_mean'] > min_y]

    # Limiter à 10
    lignes_valides = sorted(lignes_valides, key=lambda x: x['cy_mean'])[:10]

    if len(lignes_valides) == 0:
        return []

    matchs = []
    equipes_utilisees = set()

    for i, ligne in enumerate(lignes_valides):
        y_center = int(ligne['cy_mean'])
        y_start = max(0, y_center - 60)
        y_end = min(h_img, y_center + 60)

        # Zone noms (gauche)
        ligne_full = img.crop((0, y_start, w_img//2 + 50, y_end))

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

                        # CORRECTION: valeur > 20 = erreur OCR
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

        # Extraire noms d'équipes
        noms_detectes = []
        try:
            res_noms = reader.readtext(np.array(ligne_full), detail=1, paragraph=False)
            for bbox, text, prob in res_noms:
                if prob > 0.3 and len(text) > 2:
                    try:
                        cy = (bbox[0][1] + bbox[2][1]) / 2
                        noms_detectes.append((cy, text))
                    except:
                        continue
            noms_detectes.sort()
        except:
            pass

        # Assigner équipes avec verrouillage
        equipes_restantes = [t for t in engine.teams_list if t not in equipes_utilisees]

        dom_default = ""
        ext_default = ""

        if len(noms_detectes) >= 2:
            nom_dom_ocr = noms_detectes[0][1]
            nom_ext_ocr = noms_detectes[1][1]

            dom_match = get_close_matches(nom_dom_ocr, equipes_restantes, n=1, cutoff=0.5)
            if dom_match:
                dom_default = dom_match[0]
                equipes_utilisees.add(dom_default)
                equipes_restantes.remove(dom_default)

            ext_match = get_close_matches(nom_ext_ocr, equipes_restantes, n=1, cutoff=0.5)
            if ext_match:
                ext_default = ext_match[0]
                equipes_utilisees.add(ext_default)

        if not dom_default and equipes_restantes and noms_detectes:
            nom_brut = noms_detectes[0][1]
            dom_match = get_close_matches(nom_brut, equipes_restantes, n=1, cutoff=0.4)
            if dom_match:
                dom_default = dom_match[0]
                equipes_utilisees.add(dom_default)
                equipes_restantes.remove(dom_default)

        if not ext_default and equipes_restantes:
            nom_brut = noms_detectes[1][1] if len(noms_detectes) > 1 else ""
            ext_match = get_close_matches(nom_brut, equipes_restantes, n=1, cutoff=0.4)
            if ext_match:
                ext_default = ext_match[0]
                equipes_utilisees.add(ext_default)

        matchs.append({
            'index': i,
            'h': dom_default,
            'a': ext_default,
            'o': cotes_detectees,
            'ligne_img': img.crop((0, y_start, w_img, y_end))
        })

    return matchs

# ===================== OCR RÉSULTATS (NOUVEAU) =====================
def ocr_resultats_bet261(image_bytes, debug=False):
    """OCR avancé pour résultats Bet261 avec détection rectangles de score."""
    img = Image.open(io.BytesIO(image_bytes))
    img_array = np.array(img)
    h_img, w_img = img_array.shape[:2]

    import cv2
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)

    # Détecter les rectangles de score (gris foncé)
    # Gris = faible saturation, valeur moyenne-faible
    gray_mask = (hsv[:,:,1] < 50) & (hsv[:,:,2] > 40) & (hsv[:,:,2] < 180)
    gray_mask = gray_mask.astype(np.uint8)

    kernel = np.ones((5,5), np.uint8)
    gray_mask = cv2.morphologyEx(gray_mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(gray_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filtrer les rectangles de score
    rectangles = []
    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        area = bw * bh
        aspect = bw / bh if bh > 0 else 0
        # Score: carré/presque carré, taille moyenne, pas trop haut
        if 1000 < area < 8000 and 0.8 < aspect < 2.5 and bw > 40 and bh > 25:
            rectangles.append({'x': x, 'y': y, 'w': bw, 'h': bh, 'cx': x+bw//2, 'cy': y+bh//2})

    # Trier par Y et filtrer le header
    rectangles.sort(key=lambda r: r['cy'])
    min_y = int(h_img * 0.15)
    rectangles = [r for r in rectangles if r['cy'] > min_y]

    # Limiter à 10
    rectangles = rectangles[:10]

    if len(rectangles) == 0:
        return []

    matches = []

    for i, rect in enumerate(rectangles):
        y_center = rect['cy']
        y_start = max(0, y_center - 80)
        y_end = min(h_img, y_center + 80)

        # Extraire toute la ligne
        ligne_img = img.crop((0, y_start, w_img, y_end))
        ligne_array = np.array(ligne_img)

        # Définir les zones
        zone_gauche = ligne_img.crop((0, 0, w_img//2 - 20, ligne_img.size[1]))
        zone_centre = img.crop((rect['x']-10, y_start, rect['x']+rect['w']+10, y_end))
        zone_droite = ligne_img.crop((w_img//2 + 20, 0, w_img, ligne_img.size[1]))

        # OCR sur chaque zone
        # 1. Score (centre)
        score = ""
        mt = ""
        try:
            res_score = reader.readtext(np.array(zone_centre), detail=0, paragraph=False)
            if res_score:
                texte_score = ' '.join(res_score)
                # Chercher X:Y ou X-Y
                match_score = re.search(r'(\d{1,2})[:\-](\d{1,2})', texte_score)
                if match_score:
                    score = f"{match_score.group(1)}:{match_score.group(2)}"
                # Chercher MT
                match_mt = re.search(r'MT[:\s]*(\d{1,2})[:\-\.](\d{1,2})', texte_score, re.IGNORECASE)
                if match_mt:
                    mt = f"{match_mt.group(1)}:{match_mt.group(2)}"
        except:
            pass

        # 2. Équipes et buteurs (gauche et droite)
        equipe_dom = ""
        equipe_ext = ""
        buteurs_dom = ""
        buteurs_ext = ""

        try:
            # Zone gauche
            res_gauche = reader.readtext(np.array(zone_gauche), detail=1, paragraph=False)
            noms_gauche = []
            minutes_gauche = []
            for bbox, text, prob in res_gauche:
                if prob > 0.3:
                    # Chercher des minutes (XX')
                    mins = re.findall(r"(\d{1,3})'", text)
                    if mins:
                        minutes_gauche.extend(mins)
                    elif len(text) > 2:
                        noms_gauche.append(text)

            if noms_gauche:
                equipe_dom = get_close_matches(noms_gauche[0], engine.teams_list, n=1, cutoff=0.4)
                equipe_dom = equipe_dom[0] if equipe_dom else noms_gauche[0]
            if minutes_gauche:
                buteurs_dom = ' '.join(f"{m}'" for m in minutes_gauche)

            # Zone droite
            res_droite = reader.readtext(np.array(zone_droite), detail=1, paragraph=False)
            noms_droite = []
            minutes_droite = []
            for bbox, text, prob in res_droite:
                if prob > 0.3:
                    mins = re.findall(r"(\d{1,3})'", text)
                    if mins:
                        minutes_droite.extend(mins)
                    elif len(text) > 2:
                        noms_droite.append(text)

            if noms_droite:
                equipe_ext = get_close_matches(noms_droite[0], engine.teams_list, n=1, cutoff=0.4)
                equipe_ext = equipe_ext[0] if equipe_ext else noms_droite[0]
            if minutes_droite:
                buteurs_ext = ' '.join(f"{m}'" for m in minutes_droite)

        except:
            pass

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
    <div class="logo-container">
        <div class="logo-svg">{LOGO_SVG}</div>
        <div>
            <h1 class="header-title">ORACLE MAHITA</h1>
            <div class="header-subtitle">V36.0 — IA Intégrée · Apprentissage Actif · OCR Bet261</div>
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
        if rang <= 3: return ['background-color: rgba(0,255,0,0.12)'] * len(row)
        elif rang >= 17: return ['background-color: rgba(255,75,75,0.12)'] * len(row)
        return [''] * len(row)

    st.dataframe(standings.style.apply(style_classement, axis=1), use_container_width=True, hide_index=True)
    st.caption("🟢 Top 3 (Titre) · 🔴 Zone de relégation")

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

        if st.button("🔍 Lancer le scan OCR", use_container_width=True):
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

            # Vérification doublons
            toutes_equipes = []
            for m in matchs_ocr:
                toutes_equipes.extend([m['h'], m['a']])

            equipes_uniques = set(toutes_equipes)
            doublons = len(toutes_equipes) - len(equipes_uniques)

            if len(matchs_ocr) != 10:
                st.warning(f"⚠️ {len(matchs_ocr)} matchs trouvés sur 10 attendus.")

            if doublons > 0:
                st.warning(f"⚠️ {doublons} doublons d'équipes détectés. Vérifiez manuellement.")

            if len(equipes_uniques) != 20:
                manquantes = [t for t in engine.teams_list if t not in equipes_uniques]
                if manquantes:
                    st.warning(f"⚠️ Équipes manquantes : {', '.join(manquantes)}")

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

                        # Équipes disponibles (pas déjà utilisées ailleurs)
                        equipes_dom = engine.teams_list.copy()
                        equipes_ext = engine.teams_list.copy()

                        for j, other in enumerate(matchs_ocr):
                            if j != i:
                                if other['h'] and other['h'] in equipes_dom:
                                    equipes_dom.remove(other['h'])
                                if other['a'] and other['a'] in equipes_ext:
                                    equipes_ext.remove(other['a'])

                        equipe_dom = st.selectbox(
                            "Domicile",
                            equipes_dom,
                            index=equipes_dom.index(match['h']) if match['h'] in equipes_dom else 0,
                            key=f"ocr_dom_{i}"
                        )

                        equipe_ext = st.selectbox(
                            "Extérieur",
                            equipes_ext,
                            index=equipes_ext.index(match['a']) if match['a'] in equipes_ext else 0,
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

            # Validation
            if st.button("🔥 Valider et importer", use_container_width=True):
                if len(matchs_ocr) != 10:
                    st.error(f"❌ Il faut exactement 10 matchs !")
                else:
                    toutes_equipes = []
                    for m in matchs_ocr:
                        toutes_equipes.extend([m['h'], m['a']])

                    if len(toutes_equipes) != len(set(toutes_equipes)):
                        st.error("❌ Doublons d'équipes détectés ! Corrigez.")
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

                        custom_notify("✅ Calendrier importé ! Allez dans PRONOS", "#7FFFD4")
                        st.rerun()

    # ── Option 2 : Saisie manuelle ──
    st.divider()
    st.markdown("#### ✏️ Option 2 : Saisie manuelle")

    if 'tmp_cal' not in st.session_state:
        if st.button("➕ Initialiser saisie manuelle (10 matchs)"):
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
                custom_notify("✅ Calendrier enregistré ! Allez dans l'onglet PRONOS", "#7FFFD4")
                st.rerun()

# ===================== TAB 2 : PRONOS =====================
with tabs[2]:
    st.markdown("### 🎯 Pronostics — Cerveau I")

    if 'current_ready' not in st.session_state or not st.session_state.get('current_ready'):
        st.info("Veuillez d'abord enregistrer un calendrier dans l'onglet **CALENDRIER**.")
    else:
        current_ready = st.session_state['current_ready']
        j_num = st.session_state.get('current_j_num', 1)
        standings = get_standings(st.session_state['history'][s_active], engine.teams_list)

        safe_d, risque_d, fun_d = [], [], []
        all_analyses = []

        for m in current_ready:
            r_dom = int(standings[standings['Équipe'] == m['h']]['Rang'].values[0]) if not standings[standings['Équipe'] == m['h']].empty else 10
            r_ext = int(standings[standings['Équipe'] == m['a']]['Rang'].values[0]) if not standings[standings['Équipe'] == m['a']].empty else 10

            forme_dom = get_forme_equipe(st.session_state['history'], s_active, m['h'])
            forme_ext = get_forme_equipe(st.session_state['history'], s_active, m['a'])
            serie_dom = get_serie_victoires(forme_dom)
            serie_ext = get_serie_victoires(forme_ext)
            dernier_adv = get_dernier_adversaire(st.session_state['history'], s_active, m['h'])

            if oracle_brain:
                analyse = oracle_brain.analyser_match(
                    equipe_dom=m['h'], equipe_ext=m['a'], cotes=m['o'],
                    journee=j_num, rang_dom=r_dom, rang_ext=r_ext,
                    serie_dom=serie_dom, serie_ext=serie_ext,
                    forme_dom=forme_dom, forme_ext=forme_ext,
                    match_precedent_dom=dernier_adv
                )
            else:
                analyse = {
                    'choix_expert': f"{m['h']} (cote {m['o'][0]})",
                    'indice_confiance': 60,
                    'confiance': 'MOYEN'
                }

            all_analyses.append((m, analyse))

            item = {
                "txt": analyse['choix_expert'],
                "cote": max(m['o']),
                "match": f"{m['h']} vs {m['a']}",
                "indice": analyse['indice_confiance']
            }

            if analyse.get('confiance') == "BANKER":
                safe_d.append(item)
            elif analyse.get('confiance') == "RISQUE CALCULÉ":
                risque_d.append(item)
            else:
                fun_d.append(item)

        st.markdown(f"**Journée {j_num}** — Analyse de {len(current_ready)} matchs")
        for m, analyse in all_analyses:
            with st.container():
                st.markdown(f"**{m['h']} vs {m['a']}** — {analyse['choix_expert']} ({analyse['indice_confiance']}% )")
                st.caption(f"Cotes : {m['o']} | Confiance : {analyse.get('confiance', 'N/A')}")
            st.divider()

        # Sauvegarde pronos
        jk = f"Journée {j_num}"
        if jk in st.session_state['history'][s_active]:
            st.session_state['history'][s_active][jk]["pro"] = [
                {"m": a['choix_expert'], "c": m['o'], "indice": a['indice_confiance'], "classe": a.get('confiance')}
                for m, a in all_analyses
            ]
            save_db(st.session_state['history'])

        # Tickets
        c1, c2, c3 = st.columns(3)
        def show_ticket(col, title, data, emoji, css):
            with col:
                st.markdown(f"### {emoji} {title}")
                total = 1.0
                for x in data[:3]:
                    st.markdown(f"<div class='{css}'><b>{x['match']}</b><br>{x['txt']}<br>Indice: {x['indice']}%</div>", unsafe_allow_html=True)
                    total *= x['cote']
                st.info(f"Cote combinée ≈ {total:.2f}")

        show_ticket(c1, "TICKET SAFE", safe_d, "🟢", "prono-safe")
        show_ticket(c2, "TICKET RISQUE", risque_d, "🟡", "prono-risque")
        show_ticket(c3, "TICKET FUN", fun_d, "🔴", "prono-fun")

# ===================== TAB 3 : RÉSULTATS =====================
with tabs[3]:
    st.markdown("### ⚽ Saisie des Résultats")

    j_res = st.number_input("Journée", 1, 50, 1, key="j_res_input")
    f_res = st.file_uploader("📸 Capture Résultats Bet261", type=['jpg','png','jpeg'], key="res_upload")

    extracted = []
    jk = f"Journée {j_res}"
    cal_ref = st.session_state['history'][s_active].get(jk, {}).get("cal", [])

    if f_res:
        debug = st.checkbox("🔍 Mode Debug OCR", value=False)
        with st.spinner("OCR avancé en cours..."):
            extracted = ocr_resultats_bet261(f_res.getvalue(), debug=debug)

        if extracted:
            custom_notify(f"✅ {len(extracted)} matchs détectés", "#7FFFD4")
        else:
            st.warning("OCR faible. Complétez manuellement.")

    if cal_ref and len(extracted) < len(cal_ref):
        known = {(m.get('h'), m.get('a')) for m in extracted}
        for cm in cal_ref:
            if (cm['h'], cm['a']) not in known:
                extracted.append({"h": cm['h'], "a": cm['a'], "s": "", "mt": "", "hm": "", "am": ""})

    with st.form("form_resultats"):
        st.markdown("#### Correction des résultats")
        final_res = []
        for i, m in enumerate(extracted):
            st.markdown(f"**Match {i+1} : {m.get('h','?')} vs {m.get('a','?')}**")
            c1, c2 = st.columns([2, 1.5])
            score = c1.text_input("Score Final", m.get('s', '0:0'), key=f"score_{i}")
            mt_score = c2.text_input("Mi-temps", m.get('mt', ''), key=f"mt_{i}")
            b1, b2 = st.columns(2)
            hm = b1.text_input(f"Buteurs {m.get('h','')}", m.get('hm', ''), key=f"hm_{i}")
            am = b2.text_input(f"Buteurs {m.get('a','')}", m.get('am', ''), key=f"am_{i}")
            final_res.append({"h": m.get('h'), "a": m.get('a'), "s": score, "mt": mt_score, "hm": hm, "am": am})
            st.divider()

        if st.form_submit_button("✅ Enregistrer Résultats"):
            if jk not in st.session_state['history'][s_active]:
                st.session_state['history'][s_active][jk] = {"cal": cal_ref, "res": [], "pro": []}
            st.session_state['history'][s_active][jk]["res"] = final_res
            save_db(st.session_state['history'])

            # ── Apprentissage IA ──
            if IA_DISPONIBLE:
                for i, m in enumerate(final_res):
                    try:
                        sh, sa = map(int, m['s'].replace('-', ':').split(':'))
                        resultat = "1" if sh > sa else ("X" if sh == sa else "2")
                        cotes = cal_ref[i].get('o', [2.0, 3.0, 3.0]) if cal_ref and i < len(cal_ref) else [2.0, 3.0, 3.0]
                        moteur_apprentissage.analyser_pattern_cotes(cotes[0], cotes[1], cotes[2], resultat)
                        moteur_apprentissage.analyser_pattern_equipe(m['h'], "V" if resultat=="1" else ("N" if resultat=="X" else "D"), {"domicile": True})
                        moteur_apprentissage.analyser_pattern_equipe(m['a'], "V" if resultat=="2" else ("N" if resultat=="X" else "D"), {"domicile": False})
                    except: pass
                moteur_apprentissage.save()
                custom_notify("🧠 IA : Patterns mis à jour !", "#7FFFD4")

            custom_notify("✅ Résultats enregistrés !", "#00FF00")
            st.rerun()

# ===================== TAB 4 : HISTORIQUE =====================
with tabs[4]:
    st.markdown("### 📚 Historique des Journées")
    sorted_j = sorted(st.session_state['history'][s_active].keys(), 
                      key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
    for jk in sorted_j:
        with st.expander(f"📅 {jk}"):
            d = st.session_state['history'][s_active][jk]
            htabs = st.tabs(["Calendrier", "Pronos", "Résultats"])
            with htabs[0]:
                st.dataframe(pd.DataFrame(d.get("cal", [])))
            with htabs[1]:
                st.dataframe(pd.DataFrame(d.get("pro", [])))
            with htabs[2]:
                st.dataframe(pd.DataFrame(d.get("res", [])))

# ===================== TAB 5 : GESTION =====================
with tabs[5]:
    st.markdown("### ⚙️ Gestion")
    ns = st.text_input("Nouvelle saison (ex: Saison 2027)")
    if st.button("Créer Saison"):
        if ns and ns not in st.session_state['history']:
            st.session_state['history'][ns] = {}
            save_db(st.session_state['history'])
            st.rerun()

    st.divider()
    if st.button("📥 Exporter Backup"):
        st.download_button("Télécharger Backup", 
                           data=json.dumps(st.session_state['history'], indent=4, ensure_ascii=False),
                           file_name="oracle_backup.json", mime="application/json")

# ===================== TAB 6 : PERFORMANCE =====================
with tabs[6]:
    st.markdown("### 📊 Performance Oracle")
    if st.session_state['history'][s_active]:
        if oracle_brain:
            stats = oracle_brain.calculer_performance_globale(st.session_state['history'][s_active])
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Matchs analysés", stats.get("total_matchs", 0))
            c2.metric("Taux 1N2", f"{stats.get('taux_1n2', 0):.1f}%")
            c3.metric("Scores Exacts", stats.get("scores_exacts", 0))
            c4.metric("Points/Match", f"{stats.get('moyenne_points', 0):.2f}")

            rating = stats.get("rating_general", 0)
            color = "green" if rating >= 80 else "orange" if rating >= 50 else "red"
            st.progress(int(rating))
            st.markdown(f"<h2 style='color:{color};'>{rating:.1f} / 100</h2>", unsafe_allow_html=True)
        else:
            st.info("Module Cerveau I non disponible.")

        # Stats IA Apprentissage
        if IA_DISPONIBLE:
            st.divider()
            st.markdown("### 🧠 Performance IA Apprentissage")
            stats_ia = moteur_apprentissage.get_stats_apprentissage()
            c1, c2, c3 = st.columns(3)
            c1.metric("Matchs appris", stats_ia.get("total", 0))
            c2.metric("Taux réussite IA", f"{stats_ia.get('taux_reussite', 0):.1f}%")
            c3.metric("Patterns découverts", stats_ia.get("patterns_connus", 0))

# ===================== TAB 7 : ASSISTANT IA =====================
with tabs[7]:
    st.markdown("""
    <div class="main-header" style="padding: 15px; margin-bottom: 15px;">
        <h2 style="color: #7FFFD4; margin: 0;">🤖 Assistant IA Oracle</h2>
        <p style="color: #888; margin: 5px 0 0 0;">Analyse · Prédiction · Apprentissage</p>
    </div>
    """, unsafe_allow_html=True)

    if not IA_DISPONIBLE:
        st.error("❌ Modules IA non disponibles. Vérifiez que moteur_apprentissage.py et moteur_ia_chat.py sont présents.")
    else:
        # Configuration API Groq
        with st.expander("🔑 Configuration API Groq", expanded=not moteur_ia_chat.est_connecte()):
            col1, col2 = st.columns([3, 1])
            api_key_input = col1.text_input("Clé API Groq", 
                                          value=moteur_ia_chat.api_key,
                                          type="password",
                                          placeholder="gsk_...")
            if col2.button("💾 Connecter", use_container_width=True):
                if api_key_input:
                    os.environ["GROQ_API_KEY"] = api_key_input
                    moteur_ia_chat.api_key = api_key_input
                    try:
                        from groq import Groq
                        moteur_ia_chat.client = Groq(api_key=api_key_input)
                        custom_notify("✅ API Groq connectée !", "#00FF00")
                    except Exception as e:
                        st.error(f"Erreur : {e}")
                    st.rerun()

            st.markdown("""
            <small style="color: #888;">
            📝 Clé gratuite sur <a href="https://console.groq.com" target="_blank">console.groq.com</a><br>
            💡 Sans clé = mode offline avec patterns appris uniquement.
            </small>
            """, unsafe_allow_html=True)

        # Status
        status_col1, status_col2, status_col3 = st.columns(3)
        with status_col1:
            if moteur_ia_chat.est_connecte():
                st.success("🟢 IA Avancée")
            else:
                st.warning("🟡 Mode Offline")
        with status_col2:
            stats = moteur_apprentissage.get_stats_apprentissage()
            st.info(f"📊 {stats['total']} matchs appris")
        with status_col3:
            st.info(f"🎯 {stats['taux_reussite']}% réussite")

        st.divider()

        # Zone de chat
        st.markdown("### 💬 Discuter avec l'Oracle")

        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []

        # Affiche l'historique
        for msg in st.session_state.chat_messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-user">
                    <b>👤 Vous</b><br>{msg['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                css_class = "chat-bot" if msg.get("source") == "groq" else "chat-bot-offline"
                source_text = "🧠 Groq" if msg.get("source") == "groq" else "🤖 Offline"
                st.markdown(f"""
                <div class="{css_class}">
                    <b>🔮 Oracle</b> <span style="color: #888; font-size: 0.8em;">[{source_text}]</span>
                    <br>{msg['content']}
                </div>
                """, unsafe_allow_html=True)

        # Saisie
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("Votre message...", 
                                       placeholder="Ex: Analyse Liverpool vs Manchester City",
                                       label_visibility="collapsed")
            cols = st.columns([1, 1, 4])
            with cols[0]:
                envoyer = st.form_submit_button("📤 Envoyer", use_container_width=True)
            with cols[1]:
                if st.form_submit_button("🗑️ Effacer", use_container_width=True):
                    st.session_state.chat_messages = []
                    st.rerun()

        if envoyer and user_input.strip():
            st.session_state.chat_messages.append({"role": "user", "content": user_input})

            standings = get_standings(st.session_state['history'][s_active], engine.teams_list)
            moteur_ia_chat.set_contexte(
                history=st.session_state['history'],
                saison_active=s_active,
                standings=standings,
                prochaine_journee=next_j
            )

            with st.spinner("L'Oracle réfléchit..."):
                reponse = moteur_ia_chat.discuter(user_input)

            st.session_state.chat_messages.append({
                "role": "assistant", 
                "content": reponse["texte"],
                "source": reponse["source"],
                "confiance": reponse.get("confiance", 0)
            })
            st.rerun()

        # Suggestions
        st.divider()
        st.markdown("#### ⚡ Questions rapides")
        suggestions = [
            "Stats de l'IA",
            "Quels patterns découverts ?",
            "Analyse la forme de Liverpool",
            "Pronostic prochaine journée",
            "Qui est favori selon les cotes ?"
        ]
        sugg_cols = st.columns(len(suggestions))
        for i, sugg in enumerate(suggestions):
            with sugg_cols[i]:
                if st.button(sugg, key=f"sugg_{i}", use_container_width=True):
                    st.session_state.chat_messages.append({"role": "user", "content": sugg})
                    standings = get_standings(st.session_state['history'][s_active], engine.teams_list)
                    moteur_ia_chat.set_contexte(
                        history=st.session_state['history'],
                        saison_active=s_active,
                        standings=standings,
                        prochaine_journee=next_j
                    )
                    with st.spinner("Analyse..."):
                        reponse = moteur_ia_chat.discuter(sugg)
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": reponse["texte"],
                        "source": reponse["source"]
                    })
                    st.rerun()

        # Section apprentissage
        st.divider()
        st.markdown("### 🧠 Centre d'Apprentissage")

        app_col1, app_col2 = st.columns(2)
        with app_col1:
            st.markdown("#### 📊 Patterns de Cotes")
            if moteur_apprentissage.patterns:
                pattern_data = []
                for p, d in moteur_apprentissage.patterns.items():
                    if isinstance(d, dict) and "total" in d and d["total"] >= 2:
                        pattern_data.append({
                            "Pattern": p,
                            "Total": d["total"],
                            "1": f"{d.get('1',0)} ({d.get('1',0)/d['total']*100:.0f}%)",
                            "X": f"{d.get('X',0)} ({d.get('X',0)/d['total']*100:.0f}%)",
                            "2": f"{d.get('2',0)} ({d.get('2',0)/d['total']*100:.0f}%)"
                        })
                if pattern_data:
                    st.dataframe(pd.DataFrame(pattern_data), use_container_width=True, hide_index=True)
                else:
                    st.info("Jouez plus de matchs pour découvrir des patterns !")
            else:
                st.info("Aucun pattern encore. Enregistrez des résultats.")

        with app_col2:
            st.markdown("#### ⚖️ Poids des Facteurs")
            poids_df = pd.DataFrame([
                {"Facteur": k.replace("_", " ").title(), "Poids": f"{v:.3f}"}
                for k, v in moteur_apprentissage.poids.items()
            ])
            st.dataframe(poids_df, use_container_width=True, hide_index=True)

            if st.button("🔄 Réinitialiser les poids"):
                moteur_apprentissage.poids = moteur_apprentissage._init_poids()
                moteur_apprentissage.save()
                custom_notify("Poids réinitialisés !", "#FFA500")
                st.rerun()

# ===================== Sauvegarde Globale =====================
if st.button("💾 Sauvegarder tout maintenant"):
    save_db(st.session_state['history'])
    if IA_DISPONIBLE:
        moteur_apprentissage.save()
    custom_notify("Historique sauvegardé avec succès !", "#00FF00")
