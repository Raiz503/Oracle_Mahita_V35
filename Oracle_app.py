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
    text-align: center; padding: 15px; 
    background: #0E1117; margin-bottom: 20px;
    border-bottom: 3px solid #7FFFD4;
}
.logo-container {
    display: flex; align-items: center; justify-content: center; gap: 15px;
    margin-bottom: 8px;
}
.logo-svg {
    width: 50px; height: 50px;
    flex-shrink: 0;
}
.header-title {
    color: #7FFFD4; font-size: 3.5em; font-weight: 900;
    font-family: 'Orbitron', sans-serif;
    text-transform: uppercase; letter-spacing: 5px;
    text-shadow: 0 0 25px #7FFFD4, 0 0 50px rgba(127,255,212,0.6);
    line-height: 1;
}
.header-subtitle {
    color: #888; font-size: 1em; letter-spacing: 3px;
    margin-top: 5px;
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
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <!-- Fond -->
  <circle cx="50" cy="50" r="48" fill="#7FFFD4" opacity="0.15"/>
  <circle cx="50" cy="50" r="45" fill="none" stroke="#7FFFD4" stroke-width="1.5" opacity="0.6"/>
  
  <!-- Boule cristal -->
  <circle cx="50" cy="50" r="38" fill="none" stroke="#7FFFD4" stroke-width="2"/>
  <circle cx="50" cy="50" r="35" fill="#0E1117" opacity="0.8"/>
  
  <!-- Glow -->
  <circle cx="50" cy="50" r="36" fill="none" stroke="#7FFFD4" stroke-width="0.8" opacity="0.4">
    <animate attributeName="r" values="36;38;36" dur="3s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.4;0.7;0.4" dur="3s" repeatCount="indefinite"/>
  </circle>
  
  <!-- Demi-ballon -->
  <path d="M 25 50 A 25 25 0 0 1 75 50" fill="none" stroke="#7FFFD4" stroke-width="1.5"/>
  <path d="M 35 38 L 42 45 L 35 52" fill="none" stroke="#7FFFD4" stroke-width="1"/>
  <path d="M 65 38 L 58 45 L 65 52" fill="none" stroke="#7FFFD4" stroke-width="1"/>
  <path d="M 42 45 L 58 45" fill="none" stroke="#7FFFD4" stroke-width="1"/>
  
  <!-- Demi-cerveau -->
  <path d="M 50 30 Q 72 30 72 50 Q 72 70 50 70" fill="none" stroke="#00FF00" stroke-width="1.5"/>
  <circle cx="58" cy="42" r="2" fill="#00FF00"/>
  <circle cx="66" cy="48" r="2" fill="#00FF00"/>
  <circle cx="60" cy="58" r="2" fill="#00FF00"/>
  <line x1="58" y1="42" x2="66" y2="48" stroke="#00FF00" stroke-width="1"/>
  <line x1="66" y1="48" x2="60" y2="58" stroke="#00FF00" stroke-width="1"/>
  
  <!-- Étoile -->
  <polygon points="50,12 52,18 58,18 53,22 55,28 50,24 45,28 47,22 42,18 48,18" fill="#FFD700"/>
  
  <!-- Base -->
  <ellipse cx="50" cy="88" rx="15" ry="4" fill="none" stroke="#7FFFD4" stroke-width="1.5"/>
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

# ===================== OCR RÉSULTATS (CORRIGÉ V2) =====================
def ocr_resultats_bet261(image_bytes, debug=False):
    """OCR avancé pour résultats Bet261 avec détection des scores, MT et buteurs."""
    img = Image.open(io.BytesIO(image_bytes))
    img_array = np.array(img)
    h_img, w_img = img_array.shape[:2]

    import cv2
    
    # Convertir en niveaux de gris
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Détecter les rectangles de score (gris foncé)
    # Les scores sont dans des rectangles gris foncé au centre
    _, thresh = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)
    
    # Trouver les contours des rectangles de score
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    rectangles_score = []
    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        area = bw * bh
        aspect = bw / bh if bh > 0 else 0
        # Rectangle de score: carré/presque carré, taille moyenne, au centre horizontal
        if 800 < area < 8000 and 0.8 < aspect < 3.0 and bw > 30 and bh > 20:
            # Vérifier qu'il est au centre de l'image (zone des scores)
            cx = x + bw // 2
            if w_img * 0.3 < cx < w_img * 0.7:
                rectangles_score.append({
                    'x': x, 'y': y, 'w': bw, 'h': bh,
                    'cx': cx, 'cy': y + bh // 2,
                    'area': area
                })
    
    # Trier par Y (du haut vers le bas)
    rectangles_score.sort(key=lambda r: r['cy'])
    
    # Filtrer le header (trop haut)
    min_y = int(h_img * 0.12)
    rectangles_score = [r for r in rectangles_score if r['cy'] > min_y]
    
    # Limiter à 10
    rectangles_score = rectangles_score[:10]
    
    if len(rectangles_score) == 0:
        return []

    matches = []

    for i, rect in enumerate(rectangles_score):
        y_center = rect['cy']
        
        # Zone du match: centré sur le rectangle de score, étendu verticalement
        y_start = max(0, y_center - 55)
        y_end = min(h_img, y_center + 55)
        
        # Zone complète du match
        zone_match = img.crop((0, y_start, w_img, y_end))
        
        # Zones spécifiques
        zone_gauche = img.crop((0, y_start, int(w_img * 0.32), y_end))      # Domicile + buteurs
        zone_centre = img.crop((int(w_img * 0.32), y_start, int(w_img * 0.68), y_end))  # Score + MT
        zone_droite = img.crop((int(w_img * 0.68), y_start, w_img, y_end))   # Extérieur + buteurs
        
        equipe_dom = ""
        equipe_ext = ""
        score = ""
        mt = ""
        buteurs_dom = ""
        buteurs_ext = ""
        
        # 1. Détecter le score et MT (centre)
        try:
            # Améliorer le contraste pour le score
            centre_array = np.array(zone_centre)
            centre_pil = Image.fromarray(centre_array)
            enhancer = ImageEnhance.Contrast(centre_pil)
            centre_contraste = np.array(enhancer.enhance(2.5))
            
            res_centre = reader.readtext(centre_contraste, detail=0, paragraph=False)
            
            if res_centre:
                texte_centre = ' '.join(res_centre)
                
                # Chercher score final X:Y ou X-Y (dans le rectangle gris)
                # Format: "1:0" ou "2:2" ou "0:4"
                match_score = re.search(r'(\d)\s*[:\\-]\s*(\d)', texte_centre)
                if match_score:
                    score = f"{match_score.group(1)}:{match_score.group(2)}"
                
                # Chercher MT: X:Y ou MT X:Y
                match_mt = re.search(r'[Mm][Tt][:;\\s]*(\d)\s*[:\\-]\s*(\d)', texte_centre)
                if match_mt:
                    mt = f"{match_mt.group(1)}:{match_mt.group(2)}"
                
                # Si pas de MT trouvé, chercher "MT" suivi de chiffres
                if not mt:
                    match_mt2 = re.search(r'[Mm][Tt]\s*(\d)\s*[:\\-]\s*(\d)', texte_centre)
                    if match_mt2:
                        mt = f"{match_mt2.group(1)}:{match_mt2.group(2)}"
                        
        except Exception as e:
            if debug:
                print(f"Erreur score match {i+1}: {e}")
            pass
        
        # 2. Détecter équipes et buteurs (gauche et droite)
        try:
            # GAUCHE - Domicile et buteurs
            gauche_array = np.array(zone_gauche)
            gauche_pil = Image.fromarray(gauche_array)
            enhancer_g = ImageEnhance.Contrast(gauche_pil)
            gauche_contraste = np.array(enhancer_g.enhance(2.0))
            
            res_gauche = reader.readtext(gauche_contraste, detail=1, paragraph=False)
            
            # Séparer noms d'équipes et minutes
            noms_gauche = []
            minutes_gauche = []
            
            for bbox, text, prob in res_gauche:
                if prob > 0.25:
                    text = text.strip()
                    # Chercher des minutes: XX' ou XXX'
                    mins = re.findall(r"(\d{1,3})['′`]", text)
                    if mins:
                        minutes_gauche.extend(mins)
                    # Chercher des noms d'équipes (pas des chiffres seuls)
                    elif len(text) > 2 and not re.match(r'^\d+$', text):
                        noms_gauche.append(text)
            
            # Prendre le premier nom comme équipe domicile
            if noms_gauche:
                equipe_dom = get_close_matches(noms_gauche[0], engine.teams_list, n=1, cutoff=0.4)
                equipe_dom = equipe_dom[0] if equipe_dom else noms_gauche[0]
            
            # Formater les buteurs
            if minutes_gauche:
                buteurs_dom = ' '.join(f"{m}'" for m in minutes_gauche)
            
            # DROITE - Extérieur et buteurs
            droite_array = np.array(zone_droite)
            droite_pil = Image.fromarray(droite_array)
            enhancer_d = ImageEnhance.Contrast(droite_pil)
            droite_contraste = np.array(enhancer_d.enhance(2.0))
            
            res_droite = reader.readtext(droite_contraste, detail=1, paragraph=False)
            
            noms_droite = []
            minutes_droite = []
            
            for bbox, text, prob in res_droite:
                if prob > 0.25:
                    text = text.strip()
                    mins = re.findall(r"(\d{1,3})['′`]", text)
                    if mins:
                        minutes_droite.extend(mins)
                    elif len(text) > 2 and not re.match(r'^\d+$', text):
                        noms_droite.append(text)
            
            if noms_droite:
                equipe_ext = get_close_matches(noms_droite[0], engine.teams_list, n=1, cutoff=0.4)
                equipe_ext = equipe_ext[0] if equipe_ext else noms_droite[0]
            
            if minutes_droite:
                buteurs_ext = ' '.join(f"{m}'" for m in minutes_droite)
                
        except Exception as e:
            if debug:
                print(f"Erreur équipes match {i+1}: {e}")
            pass
        
        matches.append({
            'h': equipe_dom,
            'a': equipe_ext,
            's': score,
            'mt': mt,
            'hm': buteurs_dom,
            'am': buteurs_ext,
            'ligne_img': zone_match
        })

    return matches

    

# ===================== HEADER & SAISON =====================
st.markdown(f"""
<div class="main-header">
    <div class="logo-container">
        <div class="logo-svg">{LOGO_SVG}</div>
        <div>
            <h1 class="header-title">ORACLE MAHITA</h1>
            <div class="header-subtitle">V36.0 — IA Intégrée · Apprentissage Actif</div>
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
            if st.button("🔥 Valider et importer", use_container_width=True):
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

            # ═══ MOTEUR 2: IA Apprentissage (patterns cotes) ═══
            prediction_ia = None
            confiance_ia = 50
            if IA_DISPONIBLE and patterns_cotes:
                c1, cx, c2 = m['o']
                pattern_key = f"{c1:.1f}_{cx:.1f}_{c2:.1f}"
                pattern_proche = None

                for pk, pdata in patterns_cotes.items():
                    if isinstance(pdata, dict) and "total" in pdata and pdata["total"] >= 3:
                        try:
                            pc1, pcx, pc2 = map(float, pk.split('_'))
                            diff = abs(pc1-c1) + abs(pcx-cx) + abs(pc2-c2)
                            if diff < 1.5:
                                pattern_proche = pdata
                                break
                        except:
                            continue

                if pattern_proche:
                    total = pattern_proche['total']
                    p1 = pattern_proche.get('1', 0) / total
                    pX = pattern_proche.get('X', 0) / total
                    p2 = pattern_proche.get('2', 0) / total

                    if p1 > pX and p1 > p2:
                        prediction_ia = "1"
                        confiance_ia = int(p1 * 100)
                    elif p2 > p1 and p2 > pX:
                        prediction_ia = "2"
                        confiance_ia = int(p2 * 100)
                    else:
                        prediction_ia = "X"
                        confiance_ia = int(pX * 100)

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
                'details_moteurs': {
                    'cerveau': analyse_cerveau.get('choix_expert', 'N/A') if analyse_cerveau else 'Non dispo',
                    'ia': f"{prediction_ia} ({confiance_ia}%)" if prediction_ia else 'Non dispo',
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
                    st.caption(f"Classement: {m['h']} #{r_dom} vs {m['a']} #{r_ext}")

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
                    st.markdown(f"<div style='text-align:center;padding:8px;background:rgba(127,255,212,0.15);border-radius:8px;border:1px solid #7FFFD4;'>", unsafe_allow_html=True)
                    st.markdown(f"<span style='font-size:1.8em;font-weight:bold;color:#7FFFD4;'>{analyse['score_probable']}</span>", unsafe_allow_html=True)
                    st.markdown(f"</div>", unsafe_allow_html=True)

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

        if st.button("🔍 Lancer le scan OCR", use_container_width=True):
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
            if st.button("✅ Enregistrer les résultats", use_container_width=True):
                if len(final_res) != 10:
                    st.error(f"❌ Il faut exactement 10 matchs !")
                else:
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
                                moteur_apprentissage.analyser_pattern_equipe(
                                    m['h'],
                                    "V" if resultat=="1" else ("N" if resultat=="X" else "D"),
                                    {"domicile": True}
                                )
                                moteur_apprentissage.analyser_pattern_equipe(
                                    m['a'],
                                    "V" if resultat=="2" else ("N" if resultat=="X" else "D"),
                                    {"domicile": False}
                                )
                            except:
                                pass
                        moteur_apprentissage.save()
                        custom_notify("🧠 IA : Patterns mis à jour !", "#7FFFD4")

                    # Nettoyer session
                    for key in ['ocr_res_matchs', 'ocr_res_img']:
                        if key in st.session_state:
                            del st.session_state[key]

                    custom_notify("✅ Résultats enregistrés !", "#00FF00")
                    st.rerun()

    # ── Option 2 : Saisie manuelle ──
    st.divider()
    st.markdown("#### ✏️ Saisie manuelle")

    if 'tmp_res' not in st.session_state:
        if st.button("➕ Initialiser saisie manuelle (10 matchs)"):
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
                
                if 'tmp_res' in st.session_state:
                    del st.session_state['tmp_res']
                
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
