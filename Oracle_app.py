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
CHAT_FILE = "oracle_chat_history.json"

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

# ── Initialiser IA Apprentissage avec TOUT l'historique au 1er chargement ──
if IA_DISPONIBLE and not st.session_state.get('_ia_history_loaded'):
    try:
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
    <div class="logo-container">
        <div class="logo-svg">{LOGO_SVG}</div>
        <div>
            <h1 class="header-title">ORACLE MAHITA</h1>
            <div class="header-subtitle">V37.0 — IA Intégrée · Apprentissage Actif · OCR Bet261</div>
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

                # ── Apprentissage IA sur résultats manuels aussi ──
                if IA_DISPONIBLE:
                    cal_ref_m = st.session_state['history'][s_active].get(jk, {}).get("cal", [])
                    for i, m in enumerate(final_res_manual):
                        try:
                            sh, sa = map(int, m['s'].replace('-', ':').split(':'))
                            resultat = "1" if sh > sa else ("X" if sh == sa else "2")
                            cotes = cal_ref_m[i].get('o', [2.0, 3.0, 3.0]) if cal_ref_m and i < len(cal_ref_m) else [2.0, 3.0, 3.0]
                            moteur_apprentissage.analyser_pattern_cotes(cotes[0], cotes[1], cotes[2], resultat)
                            moteur_apprentissage.analyser_pattern_equipe(
                                m['h'], "V" if resultat=="1" else ("N" if resultat=="X" else "D"), {"domicile": True})
                            moteur_apprentissage.analyser_pattern_equipe(
                                m['a'], "V" if resultat=="2" else ("N" if resultat=="X" else "D"), {"domicile": False})
                        except:
                            pass
                    moteur_apprentissage.save()

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
                    if p.get('p') == res_reel:
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

    # Stats IA Apprentissage
    if IA_DISPONIBLE:
        st.divider()
        st.markdown("### 🧠 Performance IA Apprentissage")
        stats_ia = moteur_apprentissage.get_stats_apprentissage()
        c1, c2, c3 = st.columns(3)
        c1.metric("Matchs appris", stats_ia.get("total", 0))
        c2.metric("Taux réussite IA", f"{stats_ia.get('taux_reussite', 0):.1f}%")
        c3.metric("Patterns découverts", stats_ia.get("patterns_connus", 0))
        
        # Patterns détectés (même si 0 matchs appris formellement)
        st.divider()
        st.markdown("#### 📊 Patterns de Cotes (données historiques)")
        if moteur_apprentissage.patterns:
            pattern_data = []
            for p, d in moteur_apprentissage.patterns.items():
                if isinstance(d, dict) and "total" in d and d["total"] >= 1:
                    total = d["total"]
                    pattern_data.append({
                        "Pattern Cotes": p,
                        "Occurrences": total,
                        "1": f"{d.get('1',0)} ({d.get('1',0)/total*100:.0f}%)",
                        "X": f"{d.get('X',0)} ({d.get('X',0)/total*100:.0f}%)",
                        "2": f"{d.get('2',0)} ({d.get('2',0)/total*100:.0f}%)"
                    })
            if pattern_data:
                st.dataframe(pd.DataFrame(pattern_data), use_container_width=True, hide_index=True)
            else:
                st.info("Enregistrez des résultats pour voir les patterns !")
        else:
            st.info("Aucun pattern encore. Enregistrez des résultats.")

# ===================== TAB 7 : ASSISTANT IA — CHAT MESSENGER =====================
import streamlit.components.v1 as components
import datetime as _dt

with tabs[7]:
    # ══════════════════════════════════════════════════════
    # INIT
    # ══════════════════════════════════════════════════════
    if "chat_messages" not in st.session_state:
        st.session_state['chat_messages'] = load_chat_history()

    # ══════════════════════════════════════════════════════
    # ÉTAPE 1 — Récupérer le message depuis query_params
    #           ET appeler l'IA dans le MÊME rerun
    #           → 1 seul rechargement au lieu de 3
    # ══════════════════════════════════════════════════════
    def _call_ia(user_q: str):
        """Appelle l'IA et retourne la réponse. Mis en fonction pour clarté."""
        try:
            if IA_DISPONIBLE:
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
        except Exception as _ex:
            return {"texte": f"Erreur : {_ex}", "source": "offline"}
        return moteur_ia_chat.discuter(user_q) if IA_DISPONIBLE else {"texte": "Mode offline.", "source": "offline"}

    # ══════════════════════════════════════════════════════
    # SÉLECTEUR DE THÈME — Professionnel
    # ══════════════════════════════════════════════════════
    _THEMES = {
        "🟢 Vert Oracle (défaut)": {
            "hd_grad": "linear-gradient(135deg,#00FF88,#7FFFD4)",
            "hd_name_color": "#002211",
            "hd_status_color": "#003322",
            "dot_color": "#006644",
            "msgs_bg": "#071410",
            "scroll_color": "#00FF88",
            "welcome_bg": "rgba(0,255,136,.07)",
            "welcome_border": "rgba(0,255,136,.2)",
            "welcome_color": "#7FFFD4",
            "bu_u_grad": "linear-gradient(135deg,#00FF88,#00e07a)",
            "bu_u_color": "#001a0d",
            "bu_u_shadow": "rgba(0,255,136,.4)",
            "av_b_grad": "linear-gradient(135deg,#7FFFD4,#00FF88)",
            "bu_b_bg": "rgba(255,255,255,.07)",
            "bu_b_border": "rgba(127,255,212,.2)",
            "bu_b_color": "#ffffff",
            "src_lbl_color": "#00FF88",
            "typing_color": "#7FFFD4",
            "bar_bg": "#0a1e16",
            "bar_border": "rgba(0,255,136,.15)",
            "inp_bg": "rgba(255,255,255,.06)",
            "inp_border": "rgba(0,255,136,.25)",
            "inp_focus": "#00FF88",
            "inp_focus_shadow": "rgba(0,255,136,.1)",
            "inp_placeholder": "rgba(127,255,212,.4)",
            "snd_grad": "linear-gradient(135deg,#00FF88,#7FFFD4)",
            "snd_color": "#001a0d",
            "snd_shadow": "rgba(0,255,136,.5)",
            "root_shadow": "rgba(0,255,140,.2)",
            "root_border": "rgba(0,255,140,.3)",
        },
        "🔵 Bleu Professionnel": {
            "hd_grad": "linear-gradient(135deg,#1a73e8,#4fc3f7)",
            "hd_name_color": "#ffffff",
            "hd_status_color": "#cce4ff",
            "dot_color": "#81d4fa",
            "msgs_bg": "#0d1b2a",
            "scroll_color": "#1a73e8",
            "welcome_bg": "rgba(26,115,232,.08)",
            "welcome_border": "rgba(26,115,232,.25)",
            "welcome_color": "#4fc3f7",
            "bu_u_grad": "linear-gradient(135deg,#1a73e8,#1565c0)",
            "bu_u_color": "#ffffff",
            "bu_u_shadow": "rgba(26,115,232,.4)",
            "av_b_grad": "linear-gradient(135deg,#4fc3f7,#1a73e8)",
            "bu_b_bg": "rgba(255,255,255,.06)",
            "bu_b_border": "rgba(79,195,247,.2)",
            "bu_b_color": "#e8f4fd",
            "src_lbl_color": "#4fc3f7",
            "typing_color": "#4fc3f7",
            "bar_bg": "#0a1929",
            "bar_border": "rgba(26,115,232,.2)",
            "inp_bg": "rgba(255,255,255,.05)",
            "inp_border": "rgba(26,115,232,.3)",
            "inp_focus": "#4fc3f7",
            "inp_focus_shadow": "rgba(79,195,247,.15)",
            "inp_placeholder": "rgba(79,195,247,.4)",
            "snd_grad": "linear-gradient(135deg,#1a73e8,#4fc3f7)",
            "snd_color": "#ffffff",
            "snd_shadow": "rgba(26,115,232,.5)",
            "root_shadow": "rgba(26,115,232,.2)",
            "root_border": "rgba(26,115,232,.35)",
        },
        "🟣 Violet Premium": {
            "hd_grad": "linear-gradient(135deg,#7c3aed,#c084fc)",
            "hd_name_color": "#ffffff",
            "hd_status_color": "#ede9fe",
            "dot_color": "#a78bfa",
            "msgs_bg": "#0f0a1e",
            "scroll_color": "#7c3aed",
            "welcome_bg": "rgba(124,58,237,.08)",
            "welcome_border": "rgba(124,58,237,.25)",
            "welcome_color": "#c084fc",
            "bu_u_grad": "linear-gradient(135deg,#7c3aed,#6d28d9)",
            "bu_u_color": "#ffffff",
            "bu_u_shadow": "rgba(124,58,237,.4)",
            "av_b_grad": "linear-gradient(135deg,#c084fc,#7c3aed)",
            "bu_b_bg": "rgba(255,255,255,.06)",
            "bu_b_border": "rgba(192,132,252,.2)",
            "bu_b_color": "#f3e8ff",
            "src_lbl_color": "#c084fc",
            "typing_color": "#c084fc",
            "bar_bg": "#0c0818",
            "bar_border": "rgba(124,58,237,.2)",
            "inp_bg": "rgba(255,255,255,.05)",
            "inp_border": "rgba(124,58,237,.3)",
            "inp_focus": "#c084fc",
            "inp_focus_shadow": "rgba(192,132,252,.15)",
            "inp_placeholder": "rgba(192,132,252,.4)",
            "snd_grad": "linear-gradient(135deg,#7c3aed,#c084fc)",
            "snd_color": "#ffffff",
            "snd_shadow": "rgba(124,58,237,.5)",
            "root_shadow": "rgba(124,58,237,.2)",
            "root_border": "rgba(124,58,237,.35)",
        },
        "🟠 Orange Sport": {
            "hd_grad": "linear-gradient(135deg,#f97316,#fbbf24)",
            "hd_name_color": "#1a0a00",
            "hd_status_color": "#431407",
            "dot_color": "#92400e",
            "msgs_bg": "#1a0e00",
            "scroll_color": "#f97316",
            "welcome_bg": "rgba(249,115,22,.08)",
            "welcome_border": "rgba(249,115,22,.25)",
            "welcome_color": "#fbbf24",
            "bu_u_grad": "linear-gradient(135deg,#f97316,#ea580c)",
            "bu_u_color": "#ffffff",
            "bu_u_shadow": "rgba(249,115,22,.4)",
            "av_b_grad": "linear-gradient(135deg,#fbbf24,#f97316)",
            "bu_b_bg": "rgba(255,255,255,.06)",
            "bu_b_border": "rgba(251,191,36,.2)",
            "bu_b_color": "#fff7ed",
            "src_lbl_color": "#fbbf24",
            "typing_color": "#fbbf24",
            "bar_bg": "#150b00",
            "bar_border": "rgba(249,115,22,.2)",
            "inp_bg": "rgba(255,255,255,.05)",
            "inp_border": "rgba(249,115,22,.3)",
            "inp_focus": "#fbbf24",
            "inp_focus_shadow": "rgba(251,191,36,.15)",
            "inp_placeholder": "rgba(251,191,36,.4)",
            "snd_grad": "linear-gradient(135deg,#f97316,#fbbf24)",
            "snd_color": "#1a0a00",
            "snd_shadow": "rgba(249,115,22,.5)",
            "root_shadow": "rgba(249,115,22,.2)",
            "root_border": "rgba(249,115,22,.35)",
        },
        "⚪ Blanc Élégant": {
            "hd_grad": "linear-gradient(135deg,#374151,#6b7280)",
            "hd_name_color": "#ffffff",
            "hd_status_color": "#d1d5db",
            "dot_color": "#9ca3af",
            "msgs_bg": "#f9fafb",
            "scroll_color": "#374151",
            "welcome_bg": "rgba(55,65,81,.06)",
            "welcome_border": "rgba(55,65,81,.15)",
            "welcome_color": "#374151",
            "bu_u_grad": "linear-gradient(135deg,#374151,#1f2937)",
            "bu_u_color": "#ffffff",
            "bu_u_shadow": "rgba(55,65,81,.3)",
            "av_b_grad": "linear-gradient(135deg,#6b7280,#374151)",
            "bu_b_bg": "#ffffff",
            "bu_b_border": "rgba(55,65,81,.15)",
            "bu_b_color": "#111827",
            "src_lbl_color": "#374151",
            "typing_color": "#6b7280",
            "bar_bg": "#f3f4f6",
            "bar_border": "rgba(55,65,81,.15)",
            "inp_bg": "#ffffff",
            "inp_border": "rgba(55,65,81,.2)",
            "inp_focus": "#374151",
            "inp_focus_shadow": "rgba(55,65,81,.1)",
            "inp_placeholder": "rgba(55,65,81,.4)",
            "snd_grad": "linear-gradient(135deg,#374151,#6b7280)",
            "snd_color": "#ffffff",
            "snd_shadow": "rgba(55,65,81,.3)",
            "root_shadow": "rgba(55,65,81,.15)",
            "root_border": "rgba(55,65,81,.2)",
        },
    }

    if 'chat_theme' not in st.session_state:
        st.session_state['chat_theme'] = "🟢 Vert Oracle (défaut)"

    _theme_col1, _theme_col2 = st.columns([1, 3])
    with _theme_col1:
        st.markdown("<p style='color:#7FFFD4;font-size:12px;margin-bottom:2px;'>🎨 Thème du chat :</p>", unsafe_allow_html=True)
    with _theme_col2:
        _selected_theme = st.selectbox(
            "Thème", list(_THEMES.keys()),
            index=list(_THEMES.keys()).index(st.session_state['chat_theme']),
            label_visibility="collapsed", key="theme_selector_v49"
        )
        if _selected_theme != st.session_state['chat_theme']:
            st.session_state['chat_theme'] = _selected_theme
            st.rerun()

    _T = _THEMES[st.session_state['chat_theme']]

    # ══════════════════════════════════════════════════════
    # INCOMING — Message depuis le chat HTML (query_params) ou suggestions
    # ══════════════════════════════════════════════════════
    _incoming = None

    # Lire depuis query_params — envoyé par le chat HTML via window.parent.location.href
    try:
        _qraw = st.query_params.get("_ochat", None)
        if _qraw:
            # Pas de décodeURIComponent ici car Streamlit décode automatiquement
            _incoming = _qraw if isinstance(_qraw, str) else str(_qraw)
            st.query_params.pop("_ochat", None)  # nettoyer immédiatement
    except Exception:
        pass

    # Aussi vérifier pending (formulaire natif + suggestions)
    if not _incoming and st.session_state.get('_pending_chat_input'):
        _incoming = st.session_state.pop('_pending_chat_input')

    # Si un message est arrivé → traiter IA maintenant
    if _incoming:
        _already = [m.get("content","") for m in st.session_state.get('chat_messages',[])[-3:] if m.get("role")=="user"]
        if _incoming not in _already:
            _ts = __import__('datetime').datetime.now().isoformat()
            st.session_state.chat_messages.append({"role":"user","content":_incoming,"ts":_ts})
            with st.spinner("🔮 Oracle réfléchit..."):
                _rep = _call_ia(_incoming)
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": _rep.get("texte", "Pas de réponse."),
                "source": _rep.get("source", "offline"),
                "ts": __import__('datetime').datetime.now().isoformat()
            })
            save_chat_history(st.session_state.chat_messages)
            st.rerun()

    # ══════════════════════════════════════════════════════
    # RENDU — Chat Messenger avec thème dynamique
    # ══════════════════════════════════════════════════════
    _msgs = st.session_state.get('chat_messages', [])
    _msgs_json = json.dumps(_msgs, ensure_ascii=False)

    _CHAT_HTML = f"""<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{height:100%;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:transparent;}}

.root{{
  display:flex;flex-direction:column;
  height:500px;border-radius:18px;overflow:hidden;
  box-shadow:0 0 40px {_T['root_shadow']},0 8px 32px rgba(0,0,0,.4);
  border:1.5px solid {_T['root_border']};
}}

.hd{{
  background:{_T['hd_grad']};
  padding:13px 16px;display:flex;align-items:center;gap:12px;flex-shrink:0;
}}
.hd-av{{
  width:44px;height:44px;border-radius:50%;
  background:rgba(255,255,255,.3);backdrop-filter:blur(6px);
  display:flex;align-items:center;justify-content:center;
  font-size:24px;flex-shrink:0;
  box-shadow:0 2px 12px rgba(0,0,0,.2);
}}
.hd-name{{color:{_T['hd_name_color']};font-weight:800;font-size:15px;}}
.hd-status{{color:{_T['hd_status_color']};font-size:11px;margin-top:2px;display:flex;align-items:center;gap:5px;}}
.dot{{width:8px;height:8px;border-radius:50%;background:{_T['dot_color']};animation:pulse 2s infinite;}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.6;transform:scale(.85)}}}}

.msgs{{
  flex:1;overflow-y:auto;padding:14px 12px;
  display:flex;flex-direction:column;gap:10px;
  background:{_T['msgs_bg']};
  scrollbar-width:thin;scrollbar-color:{_T['scroll_color']} {_T['msgs_bg']};
}}
.msgs::-webkit-scrollbar{{width:4px;}}
.msgs::-webkit-scrollbar-thumb{{background:{_T['scroll_color']};border-radius:4px;}}

.welcome{{
  background:{_T['welcome_bg']};border:1px solid {_T['welcome_border']};
  border-radius:14px;padding:12px 14px;
  color:{_T['welcome_color']};font-size:13px;text-align:center;
}}

.bw-u{{display:flex;justify-content:flex-end;}}
.bu-u{{
  background:{_T['bu_u_grad']};
  color:{_T['bu_u_color']};
  padding:10px 15px;
  border-radius:20px 20px 4px 20px;
  max-width:78%;font-size:14px;line-height:1.45;
  word-break:break-word;font-weight:600;
  box-shadow:0 3px 16px {_T['bu_u_shadow']};
}}
.bu-u .ts{{color:rgba(0,0,0,.35);font-size:10px;margin-top:3px;text-align:right;}}

.bw-b{{display:flex;justify-content:flex-start;align-items:flex-end;gap:8px;}}
.av-b{{
  width:32px;height:32px;border-radius:50%;
  background:{_T['av_b_grad']};
  display:flex;align-items:center;justify-content:center;
  font-size:16px;flex-shrink:0;margin-bottom:2px;
}}
.bu-b{{
  background:{_T['bu_b_bg']};
  border:1px solid {_T['bu_b_border']};
  color:{_T['bu_b_color']};
  padding:10px 15px;
  border-radius:20px 20px 20px 4px;
  max-width:82%;font-size:14px;line-height:1.5;
  word-break:break-word;
}}
.src-lbl{{font-size:10px;color:{_T['src_lbl_color']};font-weight:700;margin-bottom:4px;}}
.bu-b .ts{{font-size:10px;color:rgba(127,200,180,.5);margin-top:4px;}}

.typing{{display:flex;gap:5px;align-items:center;padding:4px 2px;}}
.typing span{{
  width:9px;height:9px;border-radius:50%;
  background:{_T['typing_color']};opacity:.5;
  animation:bnc 1.1s infinite;
}}
.typing span:nth-child(2){{animation-delay:.18s;}}
.typing span:nth-child(3){{animation-delay:.36s;}}
@keyframes bnc{{0%,80%,100%{{transform:scale(.65);opacity:.3}}40%{{transform:scale(1.15);opacity:1}}}}

/* Barre de saisie */
.bar{{
  display:flex;align-items:flex-end;gap:8px;
  padding:10px 12px;
  background:{_T['bar_bg']};
  border-top:1px solid {_T['bar_border']};
  flex-shrink:0;
}}
/* BUG 2 FIX: textarea multiline au lieu de input */
.inp{{
  flex:1;min-width:0;
  background:{_T['inp_bg']};
  border:1.5px solid {_T['inp_border']};
  border-radius:18px;
  padding:10px 16px;
  font-size:14px;color:{_T['bu_b_color']};outline:none;
  transition:border-color .2s;
  resize:none;
  min-height:42px;max-height:120px;
  overflow-y:auto;
  line-height:1.4;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
}}
.inp:focus{{border-color:{_T['inp_focus']};box-shadow:0 0 0 3px {_T['inp_focus_shadow']};}}
.inp::placeholder{{color:{_T['inp_placeholder']};}}
.snd{{
  width:44px;height:44px;border-radius:50%;
  background:{_T['snd_grad']};
  border:none;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  font-size:20px;color:{_T['snd_color']};font-weight:bold;
  box-shadow:0 3px 16px {_T['snd_shadow']};
  transition:transform .15s,box-shadow .15s;flex-shrink:0;
  margin-bottom:1px;
}}
.snd:hover{{transform:scale(1.08);}}
.snd:active{{transform:scale(.9);}}
.snd:disabled{{opacity:.35;cursor:default;transform:none;}}

@media(max-width:600px){{.root{{height:420px;}}}}
</style>
</head>
<body>
<div class="root">
  <div class="hd">
    <div class="hd-av">🔮</div>
    <div style="flex:1;">
      <div class="hd-name">Oracle Mahita IA</div>
      <div class="hd-status"><span class="dot"></span> En ligne · Assistant pronostics</div>
    </div>
  </div>

  <div class="msgs" id="msgs">
    <div class="welcome">🔮 Bonjour ! Posez-moi n'importe quelle question sur vos pronostics, classements ou résultats.</div>
  </div>

  <div class="bar">
    <textarea class="inp" id="inp" placeholder="Écrivez votre message..." autocomplete="off" rows="1"></textarea>
    <button class="snd" id="snd" onclick="doSend()">&#10148;</button>
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
  let h='<div class="welcome">🔮 Bonjour ! Posez-moi n\\'importe quelle question.</div>';
  MSGS.forEach(function(m){{
    const t=fmt(m.ts||'');
    if(m.role==='user'){{
      h+='<div class="bw-u"><div class="bu-u">'+esc(m.content).replace(/\\n/g,'<br>')+'<div class="ts">'+t+'</div></div></div>';
    }}else{{
      const src=m.source==='groq'?'🧠 Groq':'🤖 Offline';
      h+='<div class="bw-b"><div class="av-b">🔮</div>'
       +'<div class="bu-b"><div class="src-lbl">'+src+'</div>'
       +esc(m.content).replace(/\\n/g,'<br>')
       +'<div class="ts">'+t+'</div></div></div>';
    }}
  }});
  box.innerHTML=h;
  box.scrollTop=box.scrollHeight;
}}

/* BUG 2 FIX: auto-resize textarea */
const inp=document.getElementById('inp');
inp.addEventListener('input',function(){{
  this.style.height='auto';
  this.style.height=Math.min(this.scrollHeight,120)+'px';
}});

function doSend(){{
  const snd=document.getElementById('snd');
  const text=inp.value.trim();
  if(!text)return;

  inp.value='';
  inp.style.height='auto';
  inp.disabled=true;
  snd.disabled=true;

  // Affichage immédiat message utilisateur + typing
  const box=document.getElementById('msgs');
  box.innerHTML+='<div class="bw-u"><div class="bu-u">'+esc(text).replace(/\\n/g,'<br>')+'</div></div>';
  box.innerHTML+='<div class="bw-b"><div class="av-b">🔮</div>'
    +'<div class="bu-b"><div class="typing"><span></span><span></span><span></span></div></div></div>';
  box.scrollTop=box.scrollHeight;

  // ✅ BUG 1 FIX: navigation vers le parent avec le message (sans double-encodage)
  try {{
    const url = new URL(window.parent.location.href);
    url.searchParams.set('_ochat', text);
    window.parent.location.href = url.toString();
  }} catch(err) {{
    // Fallback si cross-origin bloqué: réactiver le champ
    inp.disabled=false;
    snd.disabled=false;
  }}
}}

/* BUG 1 FIX: Enter envoie, Shift+Enter fait un saut de ligne */
inp.addEventListener('keydown',function(e){{
  if(e.key==='Enter' && !e.shiftKey){{e.preventDefault();doSend();}}
}});

renderAll();
</script>
</body></html>"""

    components.html(_CHAT_HTML, height=540, scrolling=False)

    st.markdown("---")

    # Formulaire Streamlit natif (backup fiable)
    st.markdown("<p style='color:#00FF88;font-size:13px;margin-bottom:4px;'>💬 Ou tapez ici :</p>", unsafe_allow_html=True)
    with st.form("chat_form_v48", clear_on_submit=True):
        _ui = st.text_input("msg", placeholder="Ex: Quelle équipe est la plus en forme ?", label_visibility="collapsed")
        _fc1, _fc2, _fc3 = st.columns([3,1,1])
        with _fc1: _submit  = st.form_submit_button("📤 Envoyer", use_container_width=True)
        with _fc2: _clear   = st.form_submit_button("🗑️ Effacer", use_container_width=True)
        with _fc3: _ctx_btn = st.form_submit_button("📋 Contexte", use_container_width=True)

    if _clear:
        st.session_state.chat_messages = []
        save_chat_history([])
        st.rerun()

    if _ctx_btn:
        try:
            _std3 = get_standings(st.session_state['history'][s_active], engine.teams_list)
            _ctx3 = build_full_context(st.session_state['history'], s_active, _std3, next_j)
            st.text_area("Contexte transmis à l'IA", _ctx3, height=200)
        except Exception as _ex3:
            st.error(f"Erreur : {_ex3}")

    if _submit and _ui.strip():
        st.session_state['_pending_chat_input'] = _ui.strip()
        st.rerun()

    # Config Groq
    with st.expander("🔑 Configuration Groq API", expanded=False):
        _c1, _c2 = st.columns([3,1])
        with _c1:
            _api_key = st.text_input("Clé API Groq",
                                     value=getattr(moteur_ia_chat,'api_key','') if IA_DISPONIBLE else '',
                                     type="password", placeholder="gsk_xxx...")
        with _c2:
            if st.button("🔗 Connecter", use_container_width=True, key="btn_groq_v48"):
                if _api_key and IA_DISPONIBLE:
                    os.environ["GROQ_API_KEY"] = _api_key
                    moteur_ia_chat.api_key = _api_key
                    try:
                        from groq import Groq
                        moteur_ia_chat.client = Groq(api_key=_api_key)
                        custom_notify("✅ Groq connecté !", "#00FF00")
                        st.rerun()
                    except Exception as _e:
                        st.error(f"Erreur : {_e}")
        _sc1, _sc2, _sc3 = st.columns(3)
        _conn = IA_DISPONIBLE and getattr(moteur_ia_chat,'est_connecte',lambda:False)()
        _sc1.success("🟢 Groq actif") if _conn else _sc1.warning("🟡 Offline")
        _sia = moteur_apprentissage.get_stats_apprentissage() if IA_DISPONIBLE else {"total":0}
        _sc2.metric("Matchs appris", _sia.get("total",0))
        _tr = sum(len(jd.get("res",[])) for sd in st.session_state['history'].values() for jd in sd.values())
        _sc3.metric("Résultats", _tr)

    # Export + effacer
    _col1, _col2 = st.columns(2)
    with _col1:
        if st.button("💾 Exporter chat", use_container_width=True, key="btn_export_v48"):
            st.download_button("📥 JSON", data=json.dumps(st.session_state.chat_messages, indent=2, ensure_ascii=False),
                               file_name="oracle_chat.json", mime="application/json")
    with _col2:
        if st.button("🗑️ Effacer historique", use_container_width=True, key="btn_clr_v48"):
            st.session_state.chat_messages = []
            save_chat_history([])
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
            if st.button(_sg, key=f"sg48_{_si}", use_container_width=True):
                st.session_state['_pending_chat_input'] = _sg
                st.rerun()

# ===================== Sauvegarde Globale =====================
# ===================== Sauvegarde Globale =====================
if st.button("💾 Sauvegarder tout maintenant", key="btn_save_all"):
    save_db(st.session_state['history'])
    if IA_DISPONIBLE:
        moteur_apprentissage.save()
    custom_notify("Historique sauvegardé avec succès !", "#00FF00")
