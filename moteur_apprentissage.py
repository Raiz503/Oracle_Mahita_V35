"""
╔══════════════════════════════════════════════════════════════╗
║           MOTEUR D'APPRENTISSAGE ORACLE                      ║
║           Détection de patterns · Poids évolutifs           ║
╚══════════════════════════════════════════════════════════════╝
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
    
    def _init_poids(self) -> Dict:
        return {
            "cote_favorite": 0.25,
            "forme_recente": 0.20,
            "classement": 0.20,
            "historique_h2h": 0.15,
            "cotes_proches": 0.10,
            "fatigue": 0.10
        }
    
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
            "patterns": self.patterns,
            "poids": self.poids,
            "historique_predictions": self.historique_predictions[-500:],
            "stats_globales": self.stats_globales
        }
        with open(DB_APPRENTISSAGE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
    
    def analyser_pattern_cotes(self, cote1: float, coteX: float, cote2: float, resultat: str):
        key = self._categoriser_cotes(cote1, coteX, cote2)
        if key not in self.patterns:
            self.patterns[key] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key][resultat] += 1
        self.patterns[key]["total"] += 1
    
    def _categoriser_cotes(self, c1: float, cX: float, c2: float) -> str:
        min_cote = min(c1, c2)
        max_cote = max(c1, c2)
        ratio = max_cote / min_cote if min_cote > 0 else 1
        if ratio < 1.3:
            return "COTES_SERREES"
        elif min(c1, c2) < 1.50:
            return "FAVORI_FORT"
        elif min(c1, c2) < 2.00:
            return "FAVORI_MODERE"
        else:
            return "MATCH_OUVERT"
    
    def get_probabilite_pattern(self, c1: float, cX: float, c2: float) -> Dict[str, float]:
        key = self._categoriser_cotes(c1, cX, c2)
        if key not in self.patterns or self.patterns[key]["total"] < 3:
            return {"1": 33.3, "X": 33.3, "2": 33.3}
        total = self.patterns[key]["total"]
        return {
            "1": round(self.patterns[key].get("1", 0) / total * 100, 1),
            "X": round(self.patterns[key].get("X", 0) / total * 100, 1),
            "2": round(self.patterns[key].get("2", 0) / total * 100, 1)
        }
    
    def analyser_pattern_equipe(self, equipe: str, resultat: str, contexte: Dict):
        if equipe not in self.patterns:
            self.patterns[equipe] = {
                "domicile": {"V": 0, "N": 0, "D": 0, "total": 0},
                "exterieur": {"V": 0, "N": 0, "D": 0, "total": 0},
                "apres_victoire": {"V": 0, "N": 0, "D": 0, "total": 0},
                "apres_defaite": {"V": 0, "N": 0, "D": 0, "total": 0}
            }
        lieu = "domicile" if contexte.get("domicile") else "exterieur"
        self.patterns[equipe][lieu][resultat] += 1
        self.patterns[equipe][lieu]["total"] += 1
    
    def enregistrer_prediction(self, match_data: Dict, prediction: str, confiance: float, resultat_reel: Optional[str] = None):
        entry = {
            "match": f"{match_data['h']} vs {match_data['a']}",
            "cotes": match_data.get('o', [0, 0, 0]),
            "prediction": prediction,
            "confiance": confiance,
            "resultat_reel": resultat_reel,
            "timestamp": self._get_timestamp()
        }
        self.historique_predictions.append(entry)
        self.stats_globales["total_matchs"] += 1
        if resultat_reel:
            self._mettre_a_jour_poids(entry, resultat_reel)
    
    def _mettre_a_jour_poids(self, prediction: Dict, resultat_reel: str):
        correct = prediction["prediction"] == resultat_reel
        if correct:
            self.stats_globales["predictions_correctes"] += 1
            if len(prediction["prediction"]) == 1:
                self.stats_globales["predictions_1n2_correctes"] += 1
            for p in self.poids:
                self.poids[p] = min(0.50, self.poids[p] * 1.02)
        else:
            for p in self.poids:
                self.poids[p] = max(0.05, self.poids[p] * 0.98)
    
    def get_stats_apprentissage(self) -> Dict:
        total = self.stats_globales["total_matchs"]
        if total == 0:
            return {"taux_reussite": 0, "total": 0, "patterns_connus": len(self.patterns)}
        return {
            "total": total,
            "taux_reussite": round(self.stats_globales["predictions_correctes"] / total * 100, 1),
            "taux_1n2": round(self.stats_globales["predictions_1n2_correctes"] / total * 100, 1),
            "poids_actuels": self.poids,
            "patterns_connus": len(self.patterns)
        }
    
    def predire_avec_apprentissage(self, match_data: Dict, contexte: Dict) -> Dict:
        c1, cX, c2 = match_data.get('o', [2.0, 3.0, 3.0])
        prob_pattern = self.get_probabilite_pattern(c1, cX, c2)
        prob_forme = contexte.get("prob_forme", {"1": 33.3, "X": 33.3, "2": 33.3})
        prob_classement = contexte.get("prob_classement", {"1": 33.3, "X": 33.3, "2": 33.3})
        
        poids = self.poids
        total_poids = poids["cote_favorite"] + poids["forme_recente"] + poids["classement"]
        final_prob = {
            "1": (prob_pattern["1"] * poids["cote_favorite"] + prob_forme["1"] * poids["forme_recente"] + prob_classement["1"] * poids["classement"]) / total_poids,
            "X": (prob_pattern["X"] * poids["cote_favorite"] + prob_forme["X"] * poids["forme_recente"] + prob_classement["X"] * poids["classement"]) / total_poids,
            "2": (prob_pattern["2"] * poids["cote_favorite"] + prob_forme["2"] * poids["forme_recente"] + prob_classement["2"] * poids["classement"]) / total_poids
        }
        
        total = final_prob["1"] + final_prob["X"] + final_prob["2"]
        if total > 0:
            final_prob = {k: round(v/total*100, 1) for k, v in final_prob.items()}
        
        choix = max(final_prob, key=final_prob.get)
        return {
            "prediction": choix,
            "probabilites": final_prob,
            "confiance": final_prob[choix],
            "facteurs": {"pattern_cotes": prob_pattern, "forme": prob_forme, "classement": prob_classement}
        }
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()
    
    def generer_rapport_patterns(self) -> str:
        lignes = ["📊 RAPPORT DES PATTERNS DÉCOUVERTS\n"]
        lignes.append(f"Total matchs : {self.stats_globales['total_matchs']}\n")
        lignes.append(f"Taux réussite : {self.get_stats_apprentissage()['taux_reussite']}%\n")
        lignes.append("-" * 40)
        for pattern, data in sorted(self.patterns.items(), key=lambda x: x[1].get("total", 0) if isinstance(x[1], dict) else 0, reverse=True)[:10]:
            if isinstance(data, dict) and "total" in data and data["total"] >= 3:
                total = data["total"]
                lignes.append(f"\n🔹 {pattern} ({total} matchs)")
                for res in ["1", "X", "2"]:
                    if res in data:
                        pct = data[res] / total * 100
                        lignes.append(f"   {res} : {pct:.1f}%")
        return "\n".join(lignes)

moteur_apprentissage = MoteurApprentissage()
