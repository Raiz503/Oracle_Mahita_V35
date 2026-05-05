"""
╔══════════════════════════════════════════════════════════════╗
║      MOTEUR IA CONVERSATIONNEL ORACLE — V2.0                ║
║      API Groq · Contexte Complet · Mémoire Session          ║
╚══════════════════════════════════════════════════════════════╝

AMÉLIORATIONS V2.0 :
  - set_contexte() accepte contexte_complet (toutes données historiques)
  - Le prompt Groq injecte l'historique complet → l'IA voit vraiment tout
  - Mémoire de session : les 6 derniers échanges sont inclus dans le prompt
    pour des conversations naturelles et cohérentes
  - _chercher_historique() cherche dans TOUTES les saisons (pas seulement l'active)
  - Nouvelle intention "historique" pour résumer les journées passées
  - Fallback offline enrichi avec les vraies données de l'historique
"""

import os
import json
import re
from typing import List, Dict, Optional
from datetime import datetime

try:
    from groq import Groq
    GROQ_DISPONIBLE = True
except ImportError:
    GROQ_DISPONIBLE = False

try:
    import streamlit as st
    STREAMLIT_DISPONIBLE = True
except ImportError:
    STREAMLIT_DISPONIBLE = False

from moteur_apprentissage import moteur_apprentissage

DB_CONVERSATIONS = "oracle_conversations.json"


class MoteurIAChat:
    def __init__(self):
        self.client = None
        self.api_key = ""
        self.conversations = self._load_conversations()

        # Contexte football (mis à jour par set_contexte)
        self.contexte_foot = {}

        # NOUVEAU : contexte complet toutes données (généré par build_full_context)
        self.contexte_complet = None

        # NOUVEAU : mémoire de session (6 derniers échanges = 12 messages)
        self.session_messages = []

        self._get_api_key()

        if GROQ_DISPONIBLE and self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except:
                pass

    # ─────────────────────────────────────────────
    #  CONFIGURATION & CONNEXION
    # ─────────────────────────────────────────────

    def _get_api_key(self):
        """Récupère la clé API de plusieurs sources possibles."""
        if STREAMLIT_DISPONIBLE:
            try:
                self.api_key = st.secrets.get("GROQ_API_KEY", "")
                if self.api_key:
                    return
            except:
                pass
        self.api_key = os.environ.get("GROQ_API_KEY", "")
        if self.api_key:
            return
        try:
            if os.path.exists(".env"):
                with open(".env", "r") as f:
                    for line in f:
                        if line.startswith("GROQ_API_KEY="):
                            self.api_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                            return
        except:
            pass

    def est_connecte(self) -> bool:
        return self.client is not None

    # ─────────────────────────────────────────────
    #  MISE À JOUR DU CONTEXTE
    # ─────────────────────────────────────────────

    def set_contexte(self,
                     history: Dict,
                     saison_active: str,
                     standings,
                     prochaine_journee: int,
                     contexte_complet: Optional[str] = None):
        """
        Met à jour le contexte football disponible pour l'IA.

        Paramètres :
            history           : dict complet {saison: {journee: {cal, res, pro}}}
            saison_active     : ex. "Saison 2026"
            standings         : DataFrame du classement actuel
            prochaine_journee : numéro de la prochaine journée
            contexte_complet  : chaîne pré-construite avec TOUTES les données.
                                Généré par build_full_context() dans Oracle_app_v39.py.
                                Si None, on reconstruit un résumé partiel en interne.
        """
        self.contexte_foot = {
            "saison": saison_active,
            "standings": standings,
            "prochaine_journee": prochaine_journee,
            "history": history
        }
        self.contexte_complet = contexte_complet

    def effacer_session(self):
        """Vide la mémoire de session (sans toucher aux conversations persistantes)."""
        self.session_messages = []

    # ─────────────────────────────────────────────
    #  POINT D'ENTRÉE PRINCIPAL
    # ─────────────────────────────────────────────

    def discuter(self, message: str, user_id: str = "default") -> Dict:
        type_demande = self._analyser_intention(message)

        if self.est_connecte():
            reponse = self._discuter_groq(message, type_demande)
            source = "groq"
        else:
            reponse = self._discuter_offline(message, type_demande)
            source = "offline"

        # Mémoriser dans la session pour les échanges suivants
        self.session_messages.append({"role": "user",      "content": message})
        self.session_messages.append({"role": "assistant", "content": reponse["texte"]})
        # Garder seulement les 12 derniers messages (6 échanges complets)
        self.session_messages = self.session_messages[-12:]

        self._sauvegarder_echange(user_id, message, reponse["texte"])

        return {
            "texte": reponse["texte"],
            "source": source,
            "analyse": reponse.get("analyse", {}),
            "confiance": reponse.get("confiance", 0)
        }

    # ─────────────────────────────────────────────
    #  CONSTRUCTION DU PROMPT SYSTÈME
    # ─────────────────────────────────────────────

    def _build_system_prompt(self) -> str:
        """
        Construit le prompt système injecté dans chaque appel Groq.
        Si contexte_complet est disponible, l'IA voit TOUT l'historique.
        Sinon, on construit un résumé partiel.
        """
        stats = moteur_apprentissage.get_stats_apprentissage()
        rapport = moteur_apprentissage.generer_rapport_patterns()

        base = (
            "Tu es Oracle Mahita, un expert en analyse footballistique et pronostics sportifs.\n"
            "Tu analyses les données avec précision et donnes des prédictions chiffrées.\n"
            "Tu es direct, technique mais pédagogue. Tu réponds TOUJOURS en français.\n"
            "Tu cites les données réelles (scores, cotes, classement) dans tes réponses.\n"
            "Tu donnes TOUJOURS un pourcentage de confiance dans tes prédictions.\n\n"
        )

        # ── Cas 1 : contexte complet disponible (Oracle_app_v39+) ──
        if self.contexte_complet:
            return (
                base
                + "DONNÉES COMPLÈTES DE L'APPLICATION :\n"
                + "=" * 60 + "\n"
                + self.contexte_complet
                + "\n" + "=" * 60 + "\n\n"
                + "PERFORMANCE IA :\n"
                + f"  • Matchs appris : {stats['total']}\n"
                + f"  • Taux de réussite : {stats['taux_reussite']}%\n"
                + f"  • Patterns connus : {stats['patterns_connus']}\n\n"
                + "Utilise ces données pour répondre avec précision. "
                + "Cite les vrais scores et équipes dans tes analyses."
            )

        # ── Cas 2 : contexte partiel (compatibilité ancienne version) ──
        ctx_lines = [
            f"Saison active : {self.contexte_foot.get('saison', 'N/A')}",
            f"Prochaine journée : J-{self.contexte_foot.get('prochaine_journee', '?')}",
            f"Matchs appris par l'IA : {stats['total']}",
            f"Taux de réussite IA : {stats['taux_reussite']}%",
            f"Patterns découverts : {stats['patterns_connus']}",
        ]

        standings = self.contexte_foot.get("standings")
        if standings is not None:
            try:
                ctx_lines.append("\nClassement (Top 10) :")
                top10 = standings.head(10)
                for _, row in top10.iterrows():
                    ctx_lines.append(
                        f"  {int(row['Rang'])}. {row['Équipe']} "
                        f"| {int(row['MJ'])} MJ "
                        f"| {int(row['Pts'])} pts "
                        f"| Diff:{int(row['Diff'])}"
                    )
            except:
                pass

        # Ajouter les 3 dernières journées depuis l'historique
        history = self.contexte_foot.get("history", {})
        saison = self.contexte_foot.get("saison", "")
        if history and saison and saison in history:
            journees = sorted(
                history[saison].keys(),
                key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0
            )
            ctx_lines.append(f"\nDernières journées :")
            for jk in journees[-3:]:
                res = history[saison][jk].get("res", [])
                if res:
                    ctx_lines.append(f"  {jk} :")
                    for r in res:
                        ctx_lines.append(f"    {r.get('h','?')} {r.get('s','?')} {r.get('a','?')}")

        ctx_lines.append(f"\nPatterns IA :\n{rapport[:600]}")

        return base + "CONTEXTE ACTUEL :\n" + "\n".join(ctx_lines)

    # ─────────────────────────────────────────────
    #  APPEL GROQ AVEC MÉMOIRE DE SESSION
    # ─────────────────────────────────────────────

    def _discuter_groq(self, message: str, type_demande: str) -> Dict:
        try:
            system_prompt = self._build_system_prompt()

            # Construire la liste de messages : system + mémoire session + nouveau message
            messages = [{"role": "system", "content": system_prompt}]

            # Injecter les échanges précédents de la session
            if self.session_messages:
                messages.extend(self.session_messages)

            messages.append({"role": "user", "content": message})

            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=1024
            )

            reponse_texte = chat_completion.choices[0].message.content
            analyse = self._extraire_analyse(reponse_texte)

            return {
                "texte": reponse_texte,
                "analyse": analyse,
                "confiance": analyse.get("confiance", 70)
            }
        except Exception as e:
            # Fallback offline si l'appel Groq échoue
            return self._discuter_offline(message, type_demande)

    # ─────────────────────────────────────────────
    #  MODE OFFLINE (enrichi)
    # ─────────────────────────────────────────────

    def _discuter_offline(self, message: str, type_demande: str) -> Dict:
        if type_demande == "prediction":
            return self._reponse_offline_prediction(message)
        elif type_demande == "analyse_match":
            return self._reponse_offline_analyse(message)
        elif type_demande in ("stats", "apprentissage"):
            return self._reponse_offline_stats()
        elif type_demande == "classement":
            return self._reponse_offline_classement()
        elif type_demande == "historique":
            return self._reponse_offline_historique()
        else:
            stats = moteur_apprentissage.get_stats_apprentissage()
            return {
                "texte": (
                    f"🤖 **Mode Offline**\n\n"
                    f"Je suis limité sans connexion Groq.\n\n"
                    f"• Matchs appris : {stats['total']}\n"
                    f"• Taux de réussite : {stats['taux_reussite']}%\n"
                    f"• Patterns connus : {stats['patterns_connus']}\n\n"
                    f"💡 Connecte-toi via l'onglet Assistant IA pour l'IA avancée."
                ),
                "confiance": 50
            }

    def _reponse_offline_prediction(self, message: str) -> Dict:
        equipes = self._extraire_equipes(message)
        if len(equipes) >= 2:
            h2h = self._chercher_historique(equipes[0], equipes[1])
            if h2h:
                return {
                    "texte": (
                        f"🤖 **Analyse Offline : {equipes[0]} vs {equipes[1]}**\n\n"
                        f"📊 Historique total : {h2h['total']} confrontations\n"
                        f"• Victoires {equipes[0]} : {h2h['v_dom']} ({h2h['pct_dom']}%)\n"
                        f"• Matchs nuls : {h2h['nuls']}\n"
                        f"• Victoires {equipes[1]} : {h2h['v_ext']} ({h2h['pct_ext']}%)\n\n"
                        f"💡 **Tendance** : {h2h['tendance']}\n\n"
                        f"⚠️ Mode offline — Connecte-toi pour une analyse complète."
                    ),
                    "confiance": 55
                }
        stats = moteur_apprentissage.get_stats_apprentissage()
        return {
            "texte": (
                f"🤖 **Mode Offline**\n\nPas assez de données H2H pour ce match.\n\n"
                f"📊 Stats globales IA : {stats['taux_reussite']}% de réussite sur {stats['total']} matchs.\n\n"
                f"💡 Connecte-toi pour une analyse approfondie."
            ),
            "confiance": 40
        }

    def _reponse_offline_analyse(self, message: str) -> Dict:
        rapport = moteur_apprentissage.generer_rapport_patterns()
        return {
            "texte": f"📊 **Analyse IA (Mode Offline)**\n\n{rapport[:1500]}\n\n⚠️ Mode offline",
            "confiance": 60
        }

    def _reponse_offline_stats(self) -> Dict:
        stats = moteur_apprentissage.get_stats_apprentissage()
        poids_str = "\n".join(
            [f"  • {k.replace('_', ' ').title()} : {v:.3f}"
             for k, v in stats.get('poids_actuels', {}).items()]
        )
        return {
            "texte": (
                f"📊 **Performance de l'IA Oracle**\n\n"
                f"• Total matchs : {stats['total']}\n"
                f"• Taux réussite : {stats['taux_reussite']}%\n"
                f"• Taux 1N2 : {stats.get('taux_1n2', 0)}%\n"
                f"• Patterns connus : {stats['patterns_connus']}\n\n"
                f"⚖️ **Poids actuels :**\n{poids_str}"
            ),
            "confiance": 85
        }

    def _reponse_offline_classement(self) -> Dict:
        standings = self.contexte_foot.get("standings")
        if standings is not None:
            try:
                lignes = ["🏆 **Classement Actuel**\n"]
                for _, row in standings.iterrows():
                    if row['Rang'] == 1:   emoji = "🥇"
                    elif row['Rang'] == 2: emoji = "🥈"
                    elif row['Rang'] == 3: emoji = "🥉"
                    else:                  emoji = f"{int(row['Rang'])}."
                    lignes.append(
                        f"{emoji} {row['Équipe']} — {int(row['Pts'])} pts "
                        f"({int(row['V'])}V {int(row['N'])}N {int(row['D'])}D | "
                        f"BP:{int(row['BP'])} BC:{int(row['BC'])})"
                    )
                return {"texte": "\n".join(lignes), "confiance": 90}
            except:
                pass
        return {
            "texte": "❌ Classement non disponible. Enregistrez d'abord des résultats.",
            "confiance": 0
        }

    def _reponse_offline_historique(self) -> Dict:
        """Résume l'historique disponible sans appel IA."""
        history = self.contexte_foot.get("history", {})
        saison = self.contexte_foot.get("saison", "")
        if not history or saison not in history:
            return {"texte": "❌ Aucun historique disponible.", "confiance": 0}

        lignes = [f"📚 **Historique — {saison}**\n"]
        journees = sorted(
            history[saison].keys(),
            key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0
        )
        for jk in journees:
            res = history[saison][jk].get("res", [])
            if res:
                lignes.append(f"\n**{jk}** ({len(res)} matchs) :")
                for r in res:
                    lignes.append(f"  {r.get('h','?')} **{r.get('s','?')}** {r.get('a','?')}")

        return {
            "texte": "\n".join(lignes) if len(lignes) > 1 else "Aucun résultat enregistré pour cette saison.",
            "confiance": 80
        }

    # ─────────────────────────────────────────────
    #  UTILITAIRES
    # ─────────────────────────────────────────────

    def _analyser_intention(self, message: str) -> str:
        msg = message.lower()
        patterns = {
            "prediction":    ["prono", "predi", "pronostic", "parier", "mise", "cote", "favori"],
            "analyse_match": ["analyse", "match", "versus", "vs", "contre"],
            "classement":    ["classement", "standings", "rang", "tableau", "position"],
            "forme":         ["forme", "série", "victoire", "défaite", "résultat"],
            "stats":         ["statistique", "stats", "pourcentage", "taux", "performance"],
            "apprentissage": ["apprend", "pattern", "découvert", "évolué", "poids"],
            "historique":    ["historique", "journée", "passé", "résumé", "résultats", "saison"],
            "aide":          ["aide", "help", "comment", "fonctionne", "explique"]
        }
        for intention, mots in patterns.items():
            if any(m in msg for m in mots):
                return intention
        return "conversation"

    def _extraire_equipes(self, message: str) -> List[str]:
        teams = [
            "Leeds", "Brighton", "A. Villa", "Manchester Blue", "C. Palace",
            "Bournemouth", "Spurs", "Burnley", "West Ham", "Liverpool",
            "Fulham", "Newcastle", "Manchester Red", "Everton", "London Blues",
            "Wolverhampton", "Sunderland", "N. Forest", "London Reds", "Brentford"
        ]
        trouvees = []
        msg_lower = message.lower()
        for team in teams:
            if team.lower() in msg_lower:
                trouvees.append(team)
        return trouvees

    def _chercher_historique(self, eq1: str, eq2: str) -> Optional[Dict]:
        """Cherche les confrontations dans TOUTES les saisons."""
        history = self.contexte_foot.get("history", {})
        if not history:
            return None

        confrontations = {"total": 0, "v_dom": 0, "v_ext": 0, "nuls": 0}

        for s_key, s_data in history.items():
            for journee_data in s_data.values():
                for match in journee_data.get("res", []):
                    h, a = match.get("h"), match.get("a")
                    if (h == eq1 and a == eq2) or (h == eq2 and a == eq1):
                        confrontations["total"] += 1
                        try:
                            sh, sa = map(int, match["s"].replace("-", ":").split(":"))
                            if h == eq1:
                                if sh > sa:   confrontations["v_dom"] += 1
                                elif sh < sa: confrontations["v_ext"] += 1
                                else:         confrontations["nuls"] += 1
                            else:
                                if sa > sh:   confrontations["v_dom"] += 1
                                elif sa < sh: confrontations["v_ext"] += 1
                                else:         confrontations["nuls"] += 1
                        except:
                            pass

        if confrontations["total"] == 0:
            return None

        total = confrontations["total"]
        confrontations["pct_dom"] = round(confrontations["v_dom"] / total * 100, 1)
        confrontations["pct_ext"] = round(confrontations["v_ext"] / total * 100, 1)

        if confrontations["v_dom"] > confrontations["v_ext"]:
            confrontations["tendance"] = f"Avantage {eq1} ({confrontations['v_dom']}V sur {total})"
        elif confrontations["v_ext"] > confrontations["v_dom"]:
            confrontations["tendance"] = f"Avantage {eq2} ({confrontations['v_ext']}V sur {total})"
        else:
            confrontations["tendance"] = "Historique très équilibré"

        return confrontations

    def _extraire_analyse(self, texte: str) -> Dict:
        analyse = {}
        conf_match = re.search(r'(\d{1,3})\s*%', texte)
        if conf_match:
            analyse["confiance"] = int(conf_match.group(1))
        pred_match = re.search(r'[Pp]ronostic.*?([1X2])', texte)
        if pred_match:
            analyse["prediction"] = pred_match.group(1)
        return analyse

    # ─────────────────────────────────────────────
    #  PERSISTANCE DES CONVERSATIONS
    # ─────────────────────────────────────────────

    def _load_conversations(self) -> List[Dict]:
        if os.path.exists(DB_CONVERSATIONS):
            try:
                with open(DB_CONVERSATIONS, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_conversations(self):
        try:
            with open(DB_CONVERSATIONS, "w", encoding="utf-8") as f:
                json.dump(self.conversations[-200:], f, indent=2, ensure_ascii=False)
        except:
            pass

    def _sauvegarder_echange(self, user_id: str, question: str, reponse: str):
        self.conversations.append({
            "user_id":   user_id,
            "question":  question,
            "reponse":   reponse,
            "timestamp": datetime.now().isoformat()
        })
        self.save_conversations()

    def get_historique_conversation(self, user_id: str = "default", limit: int = 10) -> List[Dict]:
        return [c for c in self.conversations if c.get("user_id") == user_id][-limit:]


# Instance globale
moteur_ia_chat = MoteurIAChat()
