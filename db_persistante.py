"""
╔══════════════════════════════════════════════════════════════════════════╗
║  db_persistante.py  —  Oracle Mahita V53                                ║
║  Persistance des données via GitHub API                                  ║
║                                                                          ║
║  Fonctionnement :                                                        ║
║    1. Au démarrage → charge depuis GitHub (source de vérité)            ║
║    2. À chaque save → écrit fichier local + commit sur GitHub           ║
║    3. Si GitHub injoignable → fichier local en backup                   ║
║                                                                          ║
║  Fichiers persistés :                                                    ║
║    • oracle_data.json          → historique saisons/journées            ║
║    • oracle_ia_memory.json     → patterns IA + poids adaptatifs         ║
║    • oracle_sessions.json      → clés API, préférences                  ║
║                                                                          ║
║  Configuration (Streamlit Secrets) :                                    ║
║    [github]                                                              ║
║    token = "ghp_xxxxxxxxxxxx"    ← Personal Access Token               ║
║    repo  = "votrenom/oracle_mahita_v35"                                 ║
║    branch = "main"                                                       ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import json
import os
import base64
import time
import hashlib
from typing import Any, Dict, Optional, Tuple
import streamlit as st

# ── Fichiers à persister ──────────────────────────────────────────────────
FICHIERS_PERSISTANTS = {
    "data":     "oracle_data.json",
    "ia":       "oracle_ia_memory.json",
    "sessions": "oracle_sessions.json",
}

# ── Cache mémoire pour éviter trop d'appels GitHub ───────────────────────
_cache_sha: Dict[str, str] = {}   # filename → sha du dernier commit connu
_derniere_synchro: float = 0.0    # timestamp dernière lecture GitHub


# ═══════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

def _get_config() -> Optional[Dict[str, str]]:
    """
    Lit la configuration GitHub depuis st.secrets ou variables d'environnement.
    Retourne None si non configuré (mode local uniquement).
    """
    try:
        token  = st.secrets["github"]["token"]
        repo   = st.secrets["github"]["repo"]
        branch = st.secrets["github"].get("branch", "main")
        if token and repo:
            return {"token": token, "repo": repo, "branch": branch}
    except Exception:
        pass

    # Fallback variables d'environnement
    token  = os.environ.get("GITHUB_TOKEN", "")
    repo   = os.environ.get("GITHUB_REPO", "")
    branch = os.environ.get("GITHUB_BRANCH", "main")
    if token and repo:
        return {"token": token, "repo": repo, "branch": branch}

    return None  # Mode local uniquement


def github_configure() -> bool:
    """Retourne True si GitHub est configuré et accessible."""
    return _get_config() is not None


# ═══════════════════════════════════════════════════════════════════════════
#  LECTURE GITHUB
# ═══════════════════════════════════════════════════════════════════════════

def _github_lire(filename: str) -> Tuple[Optional[Any], Optional[str]]:
    """
    Lit un fichier JSON depuis le repo GitHub.
    Retourne (data, sha) ou (None, None) en cas d'erreur.
    """
    cfg = _get_config()
    if not cfg:
        return None, None

    try:
        import requests
        url = f"https://api.github.com/repos/{cfg['repo']}/contents/{filename}"
        headers = {
            "Authorization": f"token {cfg['token']}",
            "Accept": "application/vnd.github.v3+json"
        }
        params = {"ref": cfg["branch"]}
        resp = requests.get(url, headers=headers, params=params, timeout=10)

        if resp.status_code == 200:
            info = resp.json()
            contenu_b64 = info.get("content", "")
            sha = info.get("sha", "")
            contenu = base64.b64decode(contenu_b64).decode("utf-8")
            data = json.loads(contenu)
            _cache_sha[filename] = sha
            return data, sha

        elif resp.status_code == 404:
            return {}, None  # Fichier inexistant → créer

    except Exception as e:
        print(f"[DB_PERSISTANTE] Erreur lecture GitHub '{filename}': {e}")

    return None, None


# ═══════════════════════════════════════════════════════════════════════════
#  ÉCRITURE GITHUB
# ═══════════════════════════════════════════════════════════════════════════

def _github_ecrire(filename: str, data: Any, message_commit: str = "") -> bool:
    """
    Écrit / met à jour un fichier JSON sur GitHub.
    Retourne True si succès.
    """
    cfg = _get_config()
    if not cfg:
        return False

    try:
        import requests

        contenu = json.dumps(data, indent=2, ensure_ascii=False)
        contenu_b64 = base64.b64encode(contenu.encode("utf-8")).decode("utf-8")

        if not message_commit:
            message_commit = f"Oracle Mahita — auto-save {filename}"

        url = f"https://api.github.com/repos/{cfg['repo']}/contents/{filename}"
        headers = {
            "Authorization": f"token {cfg['token']}",
            "Accept": "application/vnd.github.v3+json"
        }

        payload: Dict[str, Any] = {
            "message": message_commit,
            "content": contenu_b64,
            "branch":  cfg["branch"],
        }

        # Si on connaît le SHA actuel, l'inclure pour l'update
        sha_actuel = _cache_sha.get(filename)
        if sha_actuel:
            payload["sha"] = sha_actuel

        resp = requests.put(url, headers=headers, json=payload, timeout=15)

        if resp.status_code in (200, 201):
            # Mettre à jour le SHA en cache
            nouveau_sha = resp.json().get("content", {}).get("sha", "")
            if nouveau_sha:
                _cache_sha[filename] = nouveau_sha
            return True
        else:
            print(f"[DB_PERSISTANTE] Erreur écriture GitHub '{filename}': {resp.status_code} — {resp.text[:200]}")
            return False

    except Exception as e:
        print(f"[DB_PERSISTANTE] Exception écriture GitHub '{filename}': {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  API PUBLIQUE — LOAD / SAVE
# ═══════════════════════════════════════════════════════════════════════════

def charger_donnees(type_donnees: str = "data") -> Dict:
    """
    Charge les données depuis GitHub (priorité) ou fichier local (fallback).

    Paramètre type_donnees : "data" | "ia" | "sessions"

    Retourne un dict (vide si aucune donnée trouvée).
    """
    filename = FICHIERS_PERSISTANTS.get(type_donnees, type_donnees)

    # 1. Essai GitHub
    data_gh, sha = _github_lire(filename)
    if data_gh is not None:
        # Synchroniser le fichier local avec GitHub
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data_gh, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return data_gh

    # 2. Fallback fichier local
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {}


def sauvegarder_donnees(data: Any, type_donnees: str = "data",
                        message: str = "") -> bool:
    """
    Sauvegarde les données :
      1. Fichier local immédiatement (réponse rapide)
      2. Commit GitHub en arrière-plan

    Paramètre type_donnees : "data" | "ia" | "sessions"
    Retourne True si sauvegarde GitHub réussie, False si mode local uniquement.
    """
    filename = FICHIERS_PERSISTANTS.get(type_donnees, type_donnees)

    # Toujours sauvegarder localement d'abord
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[DB_PERSISTANTE] Erreur écriture locale '{filename}': {e}")

    # Puis commit GitHub
    if not message:
        message = f"Oracle Mahita — sauvegarde {type_donnees}"

    return _github_ecrire(filename, data, message)


# ═══════════════════════════════════════════════════════════════════════════
#  FONCTIONS DE COMMODITÉ
# ═══════════════════════════════════════════════════════════════════════════

def save_db(history: Dict) -> bool:
    """Remplace l'ancienne save_db() — drop-in replacement."""
    return sauvegarder_donnees(history, "data", "Mise à jour historique matchs")


def load_db() -> Dict:
    """Remplace l'ancienne load_db() — drop-in replacement."""
    return charger_donnees("data")


def save_ia_memory(memory_data: Dict) -> bool:
    """Sauvegarde la mémoire IA (patterns, poids, journées apprises)."""
    return sauvegarder_donnees(memory_data, "ia", "Mise à jour mémoire IA")


def load_ia_memory() -> Dict:
    """Charge la mémoire IA depuis GitHub."""
    return charger_donnees("ia")


def save_session_config(config: Dict) -> bool:
    """Sauvegarde les configurations de session (clés API, etc.)."""
    return sauvegarder_donnees(config, "sessions", "Config sessions")


def load_session_config() -> Dict:
    """Charge les configurations de session."""
    return charger_donnees("sessions")


# ═══════════════════════════════════════════════════════════════════════════
#  WIDGET STREAMLIT — STATUT DE SYNCHRONISATION
# ═══════════════════════════════════════════════════════════════════════════

def afficher_statut_sync():
    """
    Affiche un indicateur visuel de l'état de synchronisation GitHub
    à intégrer dans la sidebar ou dans un onglet Paramètres.
    """
    cfg = _get_config()
    if cfg:
        st.markdown(f"""
        <div style="padding:8px 12px;background:rgba(0,255,136,0.08);
             border:1px solid #00FF88;border-radius:8px;margin:4px 0;">
          <span style="color:#00FF88;font-weight:700;font-size:12px;">
            🔄 Sync GitHub Active
          </span><br>
          <span style="color:#888;font-size:11px;">
            Repo : {cfg['repo']} · Branche : {cfg['branch']}
          </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="padding:8px 12px;background:rgba(255,165,0,0.08);
             border:1px solid #FFA500;border-radius:8px;margin:4px 0;">
          <span style="color:#FFA500;font-weight:700;font-size:12px;">
            ⚠️ Mode Local Uniquement
          </span><br>
          <span style="color:#888;font-size:11px;">
            Configurez GitHub dans Streamlit Secrets pour persister les données.
          </span>
        </div>
        """, unsafe_allow_html=True)


def forcer_resynchronisation():
    """
    Force un rechargement depuis GitHub (utile après une intervention manuelle).
    """
    global _cache_sha
    _cache_sha.clear()
    resultats = {}
    for type_d in ["data", "ia", "sessions"]:
        data = charger_donnees(type_d)
        resultats[type_d] = len(str(data))
    return resultats
