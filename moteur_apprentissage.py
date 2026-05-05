"""
MOTEUR D'APPRENTISSAGE ORACLE — V2.0
Patterns · Poids Adaptatifs · Auto-Correction
"""

import json
import os
import re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import math

DB_APPRENTISSAGE = "oracle_ia_memory.json"


class MoteurApprentissage:
    def __init__(self):
        self.data = self._load()
        self.patterns = self.data.get("patterns", {})
        self.poids = self.data.get("poids", self._init_poids())
        self.historique_predictions = self.data.get("historique_predictions", [])
        self.stats_globales = self.data.get("stats_globales", {
            "total_matchs": 0,
            "predictions_correctes": 0,
            "predictions_1n2_correctes": 0,
            "scores_exacts": 0
        })
        self.perf_facteurs = self.data.get("perf_facteurs", self._init_perf_facteurs())

    def _init_poids(self) -> Dict:
        return {
            "cote_favorite":   0.25,
            "forme_recente":   0.20,
            "classement":      0.20,
            "historique_h2h":  0.15,
            "cotes_proches":   0.10,
            "fatigue":         0.10
        }

    def _init_perf_facteurs(self) -> Dict:
        facteurs = ["cote_favorite", "forme_recente", "classement",
                    "historique_h2h", "cotes_proches", "fatigue"]
        return {f: {"correct": 0, "total": 0} for f in facteurs}

    def _load(self) -> Dict:
        if os.path.exists(DB_APPRENTISSAGE):
            try:
                with open(DB_APPRENTISSAGE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save(self):
        self.data = {
            "patterns":               self.patterns,
            "poids":                  self.poids,
            "historique_predictions": self.historique_predictions[-500:],
            "stats_globales":         self.stats_globales,
            "perf_facteurs":          self.perf_facteurs
        }
        with open(DB_APPRENTISSAGE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    # ── Patterns cotes ──

    def analyser_pattern_cotes(self, cote1: float, coteX: float, cote2: float, resultat: str):
        # Niveau 1 : catégorie large
        key_large = self._categoriser_cotes(cote1, coteX, cote2)
        if key_large not in self.patterns:
            self.patterns[key_large] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key_large][resultat] += 1
        self.patterns[key_large]["total"] += 1

        # Niveau 2 : clé fine (arrondie à 0.1)
        key_fine = f"{round(cote1,1)}_{round(coteX,1)}_{round(cote2,1)}"
        if key_fine not in self.patterns:
            self.patterns[key_fine] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key_fine][resultat] += 1
        self.patterns[key_fine]["total"] += 1

    def _categoriser_cotes(self, c1: float, cX: float, c2: float) -> str:
        min_cote = min(c1, c2)
        max_cote = max(c1, c2)
        ratio = max_cote / min_cote if min_cote > 0 else 1
        if ratio < 1.3:
            return "COTES_SERREES"
        elif min_cote < 1.50:
            return "FAVORI_FORT"
        elif min_cote < 2.00:
            return "FAVORI_MODERE"
        else:
            return "MATCH_OUVERT"

    def get_probabilite_pattern(self, c1: float, cX: float, c2: float) -> Dict[str, float]:
        # Essai clé fine d'abord
        key_fine = f"{round(c1,1)}_{round(cX,1)}_{round(c2,1)}"
        if key_fine in self.patterns and self.patterns[key_fine]["total"] >= 3:
            total = self.patterns[key_fine]["total"]
            return {
                "1": round(self.patterns[key_fine].get("1", 0) / total * 100, 1),
                "X": round(self.patterns[key_fine].get("X", 0) / total * 100, 1),
                "2": round(self.patterns[key_fine].get("2", 0) / total * 100, 1)
            }
        # Fallback catégorie large
        key = self._categoriser_cotes(c1, cX, c2)
        if key in self.patterns and self.patterns[key]["total"] >= 3:
            total = self.patterns[key]["total"]
            return {
                "1": round(self.patterns[key].get("1", 0) / total * 100, 1),
                "X": round(self.patterns[key].get("X", 0) / total * 100, 1),
                "2": round(self.patterns[key].get("2", 0) / total * 100, 1)
            }
        return {"1": 33.3, "X": 33.3, "2": 33.3}

    # ── Patterns équipes ──

    def analyser_pattern_equipe(self, equipe: str, resultat: str, contexte: Dict):
        if equipe not in self.patterns:
            self.patterns[equipe] = {
                "domicile":       {"V": 0, "N": 0, "D": 0, "total": 0},
                "exterieur":      {"V": 0, "N": 0, "D": 0, "total": 0},
                "apres_victoire": {"V": 0, "N": 0, "D": 0, "total": 0},
                "apres_defaite":  {"V": 0, "N": 0, "D": 0, "total": 0}
            }
        lieu = "domicile" if contexte.get("domicile") else "exterieur"
        self.patterns[equipe][lieu][resultat] += 1
        self.patterns[equipe][lieu]["total"] += 1

    # ── Enregistrement & apprentissage adaptatif ──

    def enregistrer_prediction(self, match_data: Dict, prediction: str, confiance: float,
                                resultat_reel: Optional[str] = None,
                                facteurs_utilises: Optional[Dict] = None):
        entry = {
            "match":         f"{match_data['h']} vs {match_data['a']}",
            "cotes":         match_data.get('o', [0, 0, 0]),
            "prediction":    prediction,
            "confiance":     confiance,
            "resultat_reel": resultat_reel,
            "facteurs":      facteurs_utilises or {},
            "timestamp":     self._get_timestamp()
        }
        self.historique_predictions.append(entry)
        self.stats_globales["total_matchs"] += 1
        if resultat_reel:
            self._mettre_a_jour_poids(entry, resultat_reel)

    def _mettre_a_jour_poids(self, prediction: Dict, resultat_reel: str):
        """
        V2.0 — Apprentissage facteur par facteur.
        Si facteurs_utilises est fourni, on renforce/pénalise chaque facteur
        individuellement selon qu'il a bien ou mal prédit.
        """
        correct_global = (prediction["prediction"] == resultat_reel)
        if correct_global:
            self.stats_globales["predictions_correctes"] += 1
            if len(prediction["prediction"]) == 1:
                self.stats_globales["predictions_1n2_correctes"] += 1

        facteurs = prediction.get("facteurs", {})

        if facteurs:
            for facteur, pred_facteur in facteurs.items():
                if facteur not in self.poids:
                    continue
                if facteur not in self.perf_facteurs:
                    self.perf_facteurs[facteur] = {"correct": 0, "total": 0}
                self.perf_facteurs[facteur]["total"] += 1

                if pred_facteur == resultat_reel:
                    self.perf_facteurs[facteur]["correct"] += 1
                    self.poids[facteur] = min(0.50, self.poids[facteur] * 1.04)
                else:
                    self.poids[facteur] = max(0.05, self.poids[facteur] * 0.97)

            self._renormaliser_poids()
        else:
            # Compatibilité ancienne version : ajustement uniforme
            if correct_global:
                for p in self.poids:
                    self.poids[p] = min(0.50, self.poids[p] * 1.02)
            else:
                for p in self.poids:
                    self.poids[p] = max(0.05, self.poids[p] * 0.98)

    def _renormaliser_poids(self):
        total = sum(self.poids.values())
        if total > 0:
            for k in self.poids:
                self.poids[k] = round(self.poids[k] / total, 4)

    # ── Statistiques facteurs ──

    def get_meilleur_facteur(self) -> Dict:
        meilleur = None
        meilleur_taux = 0.0
        for facteur, perf in self.perf_facteurs.items():
            if perf["total"] >= 5:
                taux = perf["correct"] / perf["total"]
                if taux > meilleur_taux:
                    meilleur_taux = taux
                    meilleur = facteur
        if meilleur:
            return {
                "facteur": meilleur,
                "taux": round(meilleur_taux * 100, 1),
                "observations": self.perf_facteurs[meilleur]["total"]
            }
        return {"facteur": "non déterminé", "taux": 0, "observations": 0}

    def get_facteurs_classes(self) -> List[Dict]:
        resultats = []
        for facteur, perf in self.perf_facteurs.items():
            taux = (perf["correct"] / perf["total"] * 100) if perf["total"] > 0 else 0
            resultats.append({
                "facteur":      facteur.replace("_", " ").title(),
                "taux":         round(taux, 1),
                "poids_actuel": round(self.poids.get(facteur, 0), 3),
                "observations": perf["total"]
            })
        return sorted(resultats, key=lambda x: x["taux"], reverse=True)

    # ── Prédiction ──

    def predire_avec_apprentissage(self, match_data: Dict, contexte: Dict) -> Dict:
        c1, cX, c2  = match_data.get('o', [2.0, 3.0, 3.0])
        prob_pattern    = self.get_probabilite_pattern(c1, cX, c2)
        prob_forme      = contexte.get("prob_forme",      {"1": 33.3, "X": 33.3, "2": 33.3})
        prob_classement = contexte.get("prob_classement", {"1": 33.3, "X": 33.3, "2": 33.3})

        poids = self.poids
        total_poids = poids["cote_favorite"] + poids["forme_recente"] + poids["classement"]
        if total_poids == 0:
            total_poids = 1.0

        final_prob = {
            "1": (prob_pattern["1"]    * poids["cote_favorite"]
                + prob_forme["1"]      * poids["forme_recente"]
                + prob_classement["1"] * poids["classement"]) / total_poids,
            "X": (prob_pattern["X"]    * poids["cote_favorite"]
                + prob_forme["X"]      * poids["forme_recente"]
                + prob_classement["X"] * poids["classement"]) / total_poids,
            "2": (prob_pattern["2"]    * poids["cote_favorite"]
                + prob_forme["2"]      * poids["forme_recente"]
                + prob_classement["2"] * poids["classement"]) / total_poids,
        }

        total = sum(final_prob.values())
        if total > 0:
            final_prob = {k: round(v / total * 100, 1) for k, v in final_prob.items()}

        choix = max(final_prob, key=final_prob.get)

        pred_cote   = max(prob_pattern,    key=prob_pattern.get)
        pred_forme  = max(prob_forme,      key=prob_forme.get)
        pred_classt = max(prob_classement, key=prob_classement.get)

        return {
            "prediction":  choix,
            "probabilites": final_prob,
            "confiance":   final_prob[choix],
            "facteurs":    {
                "pattern_cotes": prob_pattern,
                "forme":         prob_forme,
                "classement":    prob_classement
            },
            "pred_par_facteur": {
                "cote_favorite": pred_cote,
                "forme_recente": pred_forme,
                "classement":    pred_classt
            }
        }

    # ── Rapports ──

    def get_stats_apprentissage(self) -> Dict:
        total = self.stats_globales["total_matchs"]
        if total == 0:
            return {
                "taux_reussite": 0, "total": 0,
                "patterns_connus": len(self.patterns),
                "taux_1n2": 0, "poids_actuels": self.poids
            }
        return {
            "total":           total,
            "taux_reussite":   round(self.stats_globales["predictions_correctes"] / total * 100, 1),
            "taux_1n2":        round(self.stats_globales["predictions_1n2_correctes"] / total * 100, 1),
            "poids_actuels":   self.poids,
            "patterns_connus": len(self.patterns)
        }

    def generer_rapport_patterns(self) -> str:
        lignes = ["RAPPORT DES PATTERNS\n"]
        lignes.append(f"Total matchs : {self.stats_globales['total_matchs']}")
        lignes.append(f"Taux réussite : {self.get_stats_apprentissage()['taux_reussite']}%")
        lignes.append("-" * 40)

        patterns_larges = {k: v for k, v in self.patterns.items()
                           if k in ("COTES_SERREES", "FAVORI_FORT", "FAVORI_MODERE", "MATCH_OUVERT")}
        autres_patterns  = {k: v for k, v in self.patterns.items()
                            if k not in patterns_larges and isinstance(v, dict) and "total" in v}

        for pattern, data in sorted(patterns_larges.items(),
                                     key=lambda x: x[1].get("total", 0), reverse=True):
            if data["total"] >= 1:
                total = data["total"]
                lignes.append(f"\n{pattern} ({total} matchs)")
                for res in ["1", "X", "2"]:
                    if res in data:
                        pct = data[res] / total * 100
                        lignes.append(f"   {res} : {pct:.1f}%")

        top_fins = sorted(
            [(k, v) for k, v in autres_patterns.items() if v.get("total", 0) >= 3],
            key=lambda x: x[1]["total"], reverse=True
        )[:5]
        if top_fins:
            lignes.append("\nPatterns fins (cotes exactes) :")
            for k, v in top_fins:
                total = v["total"]
                meilleur = max(["1", "X", "2"], key=lambda r: v.get(r, 0))
                pct = v.get(meilleur, 0) / total * 100
                lignes.append(f"   {k} → {meilleur} ({pct:.0f}% sur {total} matchs)")

        return "\n".join(lignes)

    def generer_rapport_adaptatif(self) -> str:
        lignes = ["RAPPORT D'APPRENTISSAGE ADAPTATIF\n"]
        lignes.append("Facteurs classés par fiabilité :\n")
        for f in self.get_facteurs_classes():
            obs = f["observations"]
            if obs == 0:
                statut = "Pas encore évalué"
            elif f["taux"] >= 60:
                statut = f"Fiable ({f['taux']}%)"
            elif f["taux"] >= 45:
                statut = f"Correct ({f['taux']}%)"
            else:
                statut = f"A améliorer ({f['taux']}%)"
            lignes.append(
                f"  {f['facteur']} | Poids:{f['poids_actuel']} | Obs:{obs} | {statut}"
            )
        meilleur = self.get_meilleur_facteur()
        if meilleur["observations"] > 0:
            lignes.append(
                f"\nFacteur le plus fiable : {meilleur['facteur'].replace('_', ' ').title()} "
                f"({meilleur['taux']}% sur {meilleur['observations']} matchs)"
            )
        return "\n".join(lignes)

    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()


moteur_apprentissage = MoteurApprentissage()
