"""
╔══════════════════════════════════════════════════════════════════════════════╗
║      MOTEUR D'APPRENTISSAGE ORACLE — V2.3 (COMPLET)                         ║
║  Cotes · Classement · Zones · Force · Série · Tendance Buts                ║
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
        self.perf_facteurs = self.data.get("perf_facteurs", self._init_perf_facteurs())
        # ✅ V53.2 — Anti-doublons : journées déjà apprises {saison_jkey, ...}
        self.journees_apprises: set = set(self.data.get("journees_apprises", []))

    def _init_poids(self) -> Dict:
        return {
            "cote_favorite":      0.14,
            "forme_recente":      0.11,
            "classement":         0.11,
            "classement_diff":    0.09,
            "zone_vs_zone":       0.09,   # Z1-Z4 exact
            "force_lieu":         0.08,   # fort dom / fort ext
            "lieu_rang":          0.06,   # domicile/ext + rang
            "serie_forme":        0.08,   # VVV, DDD, etc.
            "serie_rang":         0.06,   # TOP5_stable, BOT5, monte
            "tendance_buts":      0.07,   # att/def vs type adv
            "historique_h2h":     0.06,
            "cotes_proches":      0.05,
        }

    def _init_perf_facteurs(self) -> Dict:
        facteurs = ["cote_favorite", "forme_recente", "classement",
                    "classement_diff", "zone_vs_zone", "force_lieu",
                    "lieu_rang", "serie_forme", "serie_rang",
                    "tendance_buts", "historique_h2h", "cotes_proches"]
        return {f: {"correct": 0, "total": 0} for f in facteurs}

    def _load(self) -> Dict:
        # 1. Essai chargement depuis GitHub (données persistantes)
        try:
            from db_persistante import load_ia_memory
            data_gh = load_ia_memory()
            if data_gh:
                # Synchroniser le fichier local
                with open(DB_APPRENTISSAGE, "w", encoding="utf-8") as f:
                    json.dump(data_gh, f, indent=4, ensure_ascii=False)
                return data_gh
        except Exception:
            pass
        # 2. Fallback fichier local
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
            "perf_facteurs":          self.perf_facteurs,
            "journees_apprises":      list(self.journees_apprises)
        }
        # 1. Sauvegarde locale (immédiate)
        with open(DB_APPRENTISSAGE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        # 2. Sauvegarde GitHub persistante (si configuré)
        try:
            from db_persistante import save_ia_memory
            save_ia_memory(self.data)
        except Exception:
            pass  # Graceful fallback — données locales toujours disponibles

    # ═══════════════════════════════════════════════════════════
    #  ✅ V53.2 — GESTION ANTI-DOUBLONS JOURNÉES
    # ═══════════════════════════════════════════════════════════

    def _cle_journee(self, saison: str, journee_key: str) -> str:
        """Crée une clé unique {saison}::{journee} pour identifier une journée."""
        return f"{saison}::{journee_key}"

    def est_journee_apprise(self, saison: str, journee_key: str) -> bool:
        """Retourne True si cette journée a déjà été apprise."""
        return self._cle_journee(saison, journee_key) in self.journees_apprises

    def marquer_journee_apprise(self, saison: str, journee_key: str):
        """Marque une journée comme apprise après apprentissage réussi."""
        self.journees_apprises.add(self._cle_journee(saison, journee_key))

    def effacer_journee_apprise(self, saison: str, journee_key: str):
        """
        Supprime le marquage d'une journée — à appeler quand les résultats
        d'une journée sont effacés, permettant un réapprentissage propre.
        """
        self.journees_apprises.discard(self._cle_journee(saison, journee_key))

    def get_journees_apprises(self) -> List[str]:
        """Retourne la liste triée des journées déjà apprises."""
        return sorted(self.journees_apprises)

    # ═══════════════════════════════════════════════════════════
    #  HELPERS
    # ═══════════════════════════════════════════════════════════

    def _zone4(self, rang: int) -> str:
        """Zone exacte demandée : Z1(1-5), Z2(6-10), Z3(11-15), Z4(16-20)"""
        if rang <= 5:   return "Z1"
        if rang <= 10:  return "Z2"
        if rang <= 15:  return "Z3"
        return "Z4"

    def _force(self, rang: int) -> str:
        """Force : fort(1-5), medium(6-15), outsider(16-20)"""
        if rang <= 5:   return "fort"
        if rang <= 15:  return "medium"
        return "outsider"

    def _serie3(self, forme: Optional[List[str]]) -> str:
        """Extrait les 3 derniers résultats : VVN, DDD, etc."""
        if not forme or len(forme) == 0:
            return "NNN"
        last3 = forme[-3:] if len(forme) >= 3 else forme
        return "".join([str(x).upper() for x in last3])

    def _evolution_rang(self, rangs_historique: List[int]) -> str:
        """
        Détermine l'evolution du rang sur les derniers matchs.
        rands_historique = [rang_j-3, rang_j-2, rang_j-1, rang_actuel]
        """
        if not rangs_historique or len(rangs_historique) < 2:
            return "stable"
        # Regarde la tendance sur les 3 derniers enregistrements
        recent = rangs_historique[-3:]
        if len(recent) >= 2:
            delta = recent[-1] - recent[0]
            if recent[-1] <= 5:
                return "TOP5_stable"
            if recent[-1] >= 16:
                return "BOT5_stable"
            if delta <= -2:
                return "monte"
            if delta >= 2:
                return "descend"
        return "stable"

    def _profile_buts(self, bp_moy: float, bc_moy: float) -> str:
        """Profile attaque/defense : att_forte/def_faible, etc."""
        att = "forte" if bp_moy >= 2.0 else ("moyenne" if bp_moy >= 1.0 else "faible")
        def_ = "forte" if bc_moy <= 1.0 else ("moyenne" if bc_moy <= 2.0 else "faible")
        return f"att_{att}_def_{def_}"

    def _type_adversaire(self, rang: int) -> str:
        if rang <= 5:   return "favori"
        if rang <= 15:  return "medium"
        return "outsider"

    # ═══════════════════════════════════════════════════════════
    #  PATTERNS COTES (V2.1)
    # ═══════════════════════════════════════════════════════════

    def analyser_pattern_cotes(self, cote1: float, coteX: float, cote2: float, resultat: str):
        self.stats_globales["total_matchs"] += 1

        key_large = self._categoriser_cotes(cote1, coteX, cote2)
        if key_large not in self.patterns:
            self.patterns[key_large] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key_large][resultat] += 1
        self.patterns[key_large]["total"] += 1

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
        key_fine = f"{round(c1,1)}_{round(cX,1)}_{round(c2,1)}"
        if key_fine in self.patterns and self.patterns[key_fine]["total"] >= 3:
            return self._calc_probs(self.patterns[key_fine])

        for pk, pdata in self.patterns.items():
            if not isinstance(pdata, dict) or "total" not in pdata or pdata["total"] < 3:
                continue
            if "_" not in pk:
                continue
            try:
                pc1, pcx, pc2 = map(float, pk.split("_"))
                diff = abs(pc1 - c1) + abs(pcx - cX) + abs(pc2 - c2)
                if diff < 1.5:
                    return self._calc_probs(pdata)
            except:
                continue

        key_large = self._categoriser_cotes(c1, cX, c2)
        if key_large in self.patterns and self.patterns[key_large]["total"] >= 3:
            return self._calc_probs(self.patterns[key_large])

        return {"1": 33.3, "X": 33.3, "2": 33.3}

    # ═══════════════════════════════════════════════════════════
    #  PATTERNS CLASSEMENT (V2.2 adapté Z1-Z4)
    # ═══════════════════════════════════════════════════════════

    def analyser_pattern_classement(self, equipe_dom: str, equipe_ext: str,
                                     rang_dom: int, rang_ext: int, resultat: str):
        diff = rang_ext - rang_dom
        tranche_diff = self._tranche_diff(diff)
        key_diff = f"DIFF_{tranche_diff}"
        if key_diff not in self.patterns:
            self.patterns[key_diff] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key_diff][resultat] += 1
        self.patterns[key_diff]["total"] += 1

        # Zone Z1-Z4 exacte
        z_dom = self._zone4(rang_dom)
        z_ext = self._zone4(rang_ext)
        key_zone = f"ZONE_{z_dom}_vs_{z_ext}"
        if key_zone not in self.patterns:
            self.patterns[key_zone] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key_zone][resultat] += 1
        self.patterns[key_zone]["total"] += 1

    def _tranche_diff(self, diff: int) -> str:
        if diff >= 10:   return "PLUS10"
        if diff >= 5:    return "PLUS5"
        if diff >= 2:    return "PLUS2"
        if diff >= -1:   return "EGAL"
        if diff >= -4:   return "MOINS2"
        if diff >= -9:   return "MOINS5"
        return "MOINS10"

    def get_probabilite_classement(self, rang_dom: int, rang_ext: int) -> Dict[str, float]:
        diff = rang_ext - rang_dom
        z_dom = self._zone4(rang_dom)
        z_ext = self._zone4(rang_ext)

        key_zone = f"ZONE_{z_dom}_vs_{z_ext}"
        if key_zone in self.patterns and self.patterns[key_zone]["total"] >= 2:
            return self._calc_probs(self.patterns[key_zone])

        key_diff = f"DIFF_{self._tranche_diff(diff)}"
        if key_diff in self.patterns and self.patterns[key_diff]["total"] >= 2:
            return self._calc_probs(self.patterns[key_diff])

        if diff >= 5:
            return {"1": 65.0, "X": 20.0, "2": 15.0}
        elif diff >= 2:
            return {"1": 55.0, "X": 25.0, "2": 20.0}
        elif diff <= -5:
            return {"1": 15.0, "X": 20.0, "2": 65.0}
        elif diff <= -2:
            return {"1": 20.0, "X": 25.0, "2": 55.0}
        else:
            return {"1": 35.0, "X": 30.0, "2": 35.0}

    # ═══════════════════════════════════════════════════════════
    #  PATTERNS FORCE DOMICILE / EXTÉRIEUR (NOUVEAU V2.3)
    # ═══════════════════════════════════════════════════════════

    def analyser_pattern_force(self, equipe_dom: str, equipe_ext: str,
                                rang_dom: int, rang_ext: int, resultat: str):
        """
        Apprend : quand une équipe FORTE joue à domicile ou à l'extérieur.
        fort(1-5) vs medium(6-15) vs outsider(16-20)
        """
        f_dom = self._force(rang_dom)
        f_ext = self._force(rang_ext)

        # Pattern global force vs force
        key = f"FORCE_{f_dom}_dom_vs_{f_ext}_ext"
        if key not in self.patterns:
            self.patterns[key] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key][resultat] += 1
        self.patterns[key]["total"] += 1

        # Pattern équipe spécifique forte à domicile
        if f_dom == "fort":
            key_eq = f"FORTE_DOM_{equipe_dom}_vs_{f_ext}"
            if key_eq not in self.patterns:
                self.patterns[key_eq] = {"1": 0, "X": 0, "2": 0, "total": 0}
            self.patterns[key_eq][resultat] += 1
            self.patterns[key_eq]["total"] += 1

        # Pattern équipe spécifique forte à l'extérieur
        if f_ext == "fort":
            key_eq = f"FORTE_EXT_{equipe_ext}_vs_{f_dom}"
            if key_eq not in self.patterns:
                self.patterns[key_eq] = {"1": 0, "X": 0, "2": 0, "total": 0}
            self.patterns[key_eq][resultat] += 1
            self.patterns[key_eq]["total"] += 1

    def get_probabilite_force(self, rang_dom: int, rang_ext: int,
                               equipe_dom: str, equipe_ext: str) -> Dict[str, float]:
        f_dom = self._force(rang_dom)
        f_ext = self._force(rang_ext)

        # 1) Pattern spécifique équipe forte dom
        if f_dom == "fort":
            key_eq = f"FORTE_DOM_{equipe_dom}_vs_{f_ext}"
            if key_eq in self.patterns and self.patterns[key_eq]["total"] >= 2:
                return self._calc_probs(self.patterns[key_eq])

        # 2) Pattern spécifique équipe forte ext
        if f_ext == "fort":
            key_eq = f"FORTE_EXT_{equipe_ext}_vs_{f_dom}"
            if key_eq in self.patterns and self.patterns[key_eq]["total"] >= 2:
                return self._calc_probs(self.patterns[key_eq])

        # 3) Pattern général force vs force
        key = f"FORCE_{f_dom}_dom_vs_{f_ext}_ext"
        if key in self.patterns and self.patterns[key]["total"] >= 2:
            return self._calc_probs(self.patterns[key])

        # Fallback logique
        if f_dom == "fort" and f_ext == "outsider":
            return {"1": 70.0, "X": 18.0, "2": 12.0}
        if f_dom == "outsider" and f_ext == "fort":
            return {"1": 12.0, "X": 18.0, "2": 70.0}
        if f_dom == "fort" and f_ext == "medium":
            return {"1": 58.0, "X": 22.0, "2": 20.0}
        if f_dom == "medium" and f_ext == "fort":
            return {"1": 22.0, "X": 25.0, "2": 53.0}
        if f_dom == "medium" and f_ext == "outsider":
            return {"1": 55.0, "X": 25.0, "2": 20.0}
        if f_dom == "outsider" and f_ext == "medium":
            return {"1": 20.0, "X": 25.0, "2": 55.0}
        return {"1": 38.0, "X": 28.0, "2": 34.0}

    # ═══════════════════════════════════════════════════════════
    #  PATTERNS LIEU + RANG (NOUVEAU V2.3)
    # ═══════════════════════════════════════════════════════════

    def analyser_pattern_lieu_rang(self, equipe_dom: str, equipe_ext: str,
                                    rang_dom: int, rang_ext: int, resultat: str):
        """
        Domicile de rang X contre Extérieur de rang Y.
        Capture l'avantage domicile combiné au classement exact.
        """
        z_dom = self._zone4(rang_dom)
        z_ext = self._zone4(rang_ext)

        key = f"LIEU_dom_{z_dom}_vs_{z_ext}"
        if key not in self.patterns:
            self.patterns[key] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key][resultat] += 1
        self.patterns[key]["total"] += 1

        # Avantage domicile par zone
        key_av = f"AVANTAGE_dom_{z_dom}"
        if key_av not in self.patterns:
            self.patterns[key_av] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key_av][resultat] += 1
        self.patterns[key_av]["total"] += 1

    def get_probabilite_lieu_rang(self, rang_dom: int, rang_ext: int) -> Dict[str, float]:
        z_dom = self._zone4(rang_dom)
        z_ext = self._zone4(rang_ext)

        key = f"LIEU_dom_{z_dom}_vs_{z_ext}"
        if key in self.patterns and self.patterns[key]["total"] >= 2:
            return self._calc_probs(self.patterns[key])

        key_av = f"AVANTAGE_dom_{z_dom}"
        if key_av in self.patterns and self.patterns[key_av]["total"] >= 2:
            return self._calc_probs(self.patterns[key_av])

        # Fallback : avantage domicile classique
        return {"1": 45.0, "X": 28.0, "2": 27.0}

    # ═══════════════════════════════════════════════════════════
    #  PATTERNS SÉRIE DE VICTOIRES (NOUVEAU V2.3)
    # ═══════════════════════════════════════════════════════════

    def analyser_pattern_serie_forme(self, equipe_dom: str, equipe_ext: str,
                                      serie_dom: Optional[List[str]],
                                      serie_ext: Optional[List[str]], resultat: str):
        """
        Apprend selon la forme récente (3 derniers matchs).
        Ex: VVV, VVN, DDD, VDN, etc.
        """
        s_dom = self._serie3(serie_dom)
        s_ext = self._serie3(serie_ext)

        # Pattern croisé série dom vs série ext
        key = f"SERIE_{s_dom}_vs_{s_ext}"
        if key not in self.patterns:
            self.patterns[key] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key][resultat] += 1
        self.patterns[key]["total"] += 1

        # Pattern domicile seul
        key_d = f"SERIE_dom_{s_dom}"
        if key_d not in self.patterns:
            self.patterns[key_d] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key_d][resultat] += 1
        self.patterns[key_d]["total"] += 1

        # Pattern extérieur seul
        key_e = f"SERIE_ext_{s_ext}"
        if key_e not in self.patterns:
            self.patterns[key_e] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key_e][resultat] += 1
        self.patterns[key_e]["total"] += 1

    def get_probabilite_serie_forme(self, serie_dom: Optional[List[str]],
                                     serie_ext: Optional[List[str]]) -> Dict[str, float]:
        s_dom = self._serie3(serie_dom)
        s_ext = self._serie3(serie_ext)

        key = f"SERIE_{s_dom}_vs_{s_ext}"
        if key in self.patterns and self.patterns[key]["total"] >= 2:
            return self._calc_probs(self.patterns[key])

        key_d = f"SERIE_dom_{s_dom}"
        if key_d in self.patterns and self.patterns[key_d]["total"] >= 2:
            return self._calc_probs(self.patterns[key_d])

        key_e = f"SERIE_ext_{s_ext}"
        if key_e in self.patterns and self.patterns[key_e]["total"] >= 2:
            return self._calc_probs(self.patterns[key_e])

        # Fallback logique
        v_dom = s_dom.count("V")
        d_dom = s_dom.count("D")
        v_ext = s_ext.count("V")
        d_ext = s_ext.count("D")

        force_dom = v_dom - d_dom
        force_ext = v_ext - d_ext

        if force_dom >= 2 and force_ext <= -1:
            return {"1": 60.0, "X": 22.0, "2": 18.0}
        if force_ext >= 2 and force_dom <= -1:
            return {"1": 18.0, "X": 22.0, "2": 60.0}
        if force_dom >= 2:
            return {"1": 52.0, "X": 25.0, "2": 23.0}
        if force_ext >= 2:
            return {"1": 23.0, "X": 25.0, "2": 52.0}
        return {"1": 38.0, "X": 30.0, "2": 32.0}

    # ═══════════════════════════════════════════════════════════
    #  PATTERNS SÉRIE DE RANGS (NOUVEAU V2.3)
    # ═══════════════════════════════════════════════════════════

    def analyser_pattern_serie_rang(self, equipe_dom: str, equipe_ext: str,
                                     evolution_dom: str, evolution_ext: str, resultat: str):
        """
        Apprend selon l'evolution du rang : TOP5_stable, BOT5_stable, monte, descend, stable.
        """
        key = f"RANGEV_{evolution_dom}_vs_{evolution_ext}"
        if key not in self.patterns:
            self.patterns[key] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key][resultat] += 1
        self.patterns[key]["total"] += 1

        # Pattern individuel
        for ev, eq, prefix in [(evolution_dom, equipe_dom, "DOM"), (evolution_ext, equipe_ext, "EXT")]:
            key_eq = f"RANGEV_{prefix}_{eq}_{ev}"
            if key_eq not in self.patterns:
                self.patterns[key_eq] = {"1": 0, "X": 0, "2": 0, "total": 0}
            self.patterns[key_eq][resultat] += 1
            self.patterns[key_eq]["total"] += 1

    def get_probabilite_serie_rang(self, equipe_dom: str, equipe_ext: str,
                                    evolution_dom: str, evolution_ext: str) -> Dict[str, float]:
        key = f"RANGEV_{evolution_dom}_vs_{evolution_ext}"
        if key in self.patterns and self.patterns[key]["total"] >= 2:
            return self._calc_probs(self.patterns[key])

        for ev, eq, prefix in [(evolution_dom, equipe_dom, "DOM"), (evolution_ext, equipe_ext, "EXT")]:
            key_eq = f"RANGEV_{prefix}_{eq}_{ev}"
            if key_eq in self.patterns and self.patterns[key_eq]["total"] >= 2:
                return self._calc_probs(self.patterns[key_eq])

        # Fallback
        if evolution_dom == "TOP5_stable" and evolution_ext == "BOT5_stable":
            return {"1": 65.0, "X": 20.0, "2": 15.0}
        if evolution_dom == "BOT5_stable" and evolution_ext == "TOP5_stable":
            return {"1": 15.0, "X": 20.0, "2": 65.0}
        if evolution_dom == "monte":
            return {"1": 50.0, "X": 26.0, "2": 24.0}
        if evolution_ext == "monte":
            return {"1": 24.0, "X": 26.0, "2": 50.0}
        return {"1": 38.0, "X": 28.0, "2": 34.0}

    # ═══════════════════════════════════════════════════════════
    #  PATTERNS TENDANCE BUTS (NOUVEAU V2.3)
    # ═══════════════════════════════════════════════════════════

    def analyser_pattern_tendance_buts(self, equipe_dom: str, equipe_ext: str,
                                        bp_moy_dom: float, bc_moy_dom: float,
                                        bp_moy_ext: float, bc_moy_ext: float,
                                        type_adv_dom: str, type_adv_ext: str,
                                        resultat: str):
        """
        Apprend les profils offensifs/défensifs et leur efficacité face à un type d'adversaire.
        type_adv = "favori", "medium", "outsider"
        """
        prof_dom = self._profile_buts(bp_moy_dom, bc_moy_dom)
        prof_ext = self._profile_buts(bp_moy_ext, bc_moy_ext)

        # 1) Profile global dom vs ext
        key = f"TEND_{prof_dom}_vs_{prof_ext}"
        if key not in self.patterns:
            self.patterns[key] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key][resultat] += 1
        self.patterns[key]["total"] += 1

        # 2) Attaque domicile face à type adversaire extérieur
        key2 = f"TENDADV_dom_{prof_dom}_vs_{type_adv_ext}"
        if key2 not in self.patterns:
            self.patterns[key2] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key2][resultat] += 1
        self.patterns[key2]["total"] += 1

        # 3) Attaque extérieure face à type adversaire domicile
        key3 = f"TENDADV_ext_{prof_ext}_vs_{type_adv_dom}"
        if key3 not in self.patterns:
            self.patterns[key3] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key3][resultat] += 1
        self.patterns[key3]["total"] += 1

        # 4) Équipe spécifique : attaque domicile
        key4 = f"TENDEQ_dom_{equipe_dom}_{prof_dom}_vs_{type_adv_ext}"
        if key4 not in self.patterns:
            self.patterns[key4] = {"1": 0, "X": 0, "2": 0, "total": 0}
        self.patterns[key4][resultat] += 1
        self.patterns[key4]["total"] += 1

    def get_probabilite_tendance_buts(self, equipe_dom: str, equipe_ext: str,
                                       bp_moy_dom: float, bc_moy_dom: float,
                                       bp_moy_ext: float, bc_moy_ext: float,
                                       type_adv_dom: str, type_adv_ext: str) -> Dict[str, float]:
        prof_dom = self._profile_buts(bp_moy_dom, bc_moy_dom)
        prof_ext = self._profile_buts(bp_moy_ext, bc_moy_ext)

        # 1) Équipe spécifique domicile
        key4 = f"TENDEQ_dom_{equipe_dom}_{prof_dom}_vs_{type_adv_ext}"
        if key4 in self.patterns and self.patterns[key4]["total"] >= 2:
            return self._calc_probs(self.patterns[key4])

        # 2) Attaque dom vs type adv ext
        key2 = f"TENDADV_dom_{prof_dom}_vs_{type_adv_ext}"
        if key2 in self.patterns and self.patterns[key2]["total"] >= 2:
            return self._calc_probs(self.patterns[key2])

        # 3) Attaque ext vs type adv dom
        key3 = f"TENDADV_ext_{prof_ext}_vs_{type_adv_dom}"
        if key3 in self.patterns and self.patterns[key3]["total"] >= 2:
            return self._calc_probs(self.patterns[key3])

        # 4) Profile global
        key = f"TEND_{prof_dom}_vs_{prof_ext}"
        if key in self.patterns and self.patterns[key]["total"] >= 2:
            return self._calc_probs(self.patterns[key])

        # Fallback logique
        if "att_forte" in prof_dom and "def_faible" in prof_ext:
            return {"1": 62.0, "X": 20.0, "2": 18.0}
        if "att_forte" in prof_ext and "def_faible" in prof_dom:
            return {"1": 18.0, "X": 20.0, "2": 62.0}
        if "att_faible" in prof_dom and "att_faible" in prof_ext:
            return {"1": 28.0, "X": 40.0, "2": 32.0}
        return {"1": 40.0, "X": 28.0, "2": 32.0}

    # ═══════════════════════════════════════════════════════════
    #  PATTERNS EQUIPES (existant)
    # ═══════════════════════════════════════════════════════════

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

    # ═══════════════════════════════════════════════════════════
    #  UTILITAIRES COMMUNS
    # ═══════════════════════════════════════════════════════════

    def _calc_probs(self, data: dict) -> Dict[str, float]:
        total = data["total"]
        return {
            "1": round(data.get("1", 0) / total * 100, 1),
            "X": round(data.get("X", 0) / total * 100, 1),
            "2": round(data.get("2", 0) / total * 100, 1)
        }

    # ═══════════════════════════════════════════════════════════
    #  ENREGISTREMENT & APPRENTISSAGE ADAPTATIF
    # ═══════════════════════════════════════════════════════════

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

    # ═══════════════════════════════════════════════════════════
    #  PREDICTION UNIFIÉE (V2.3)
    # ═══════════════════════════════════════════════════════════

    def predire_avec_apprentissage(self, match_data: Dict, contexte: Dict) -> Dict:
        c1, cX, c2 = match_data.get('o', [2.0, 3.0, 3.0])
        rang_dom = contexte.get("rang_dom", 10)
        rang_ext = contexte.get("rang_ext", 10)
        equipe_dom = match_data.get('h', '')
        equipe_ext = match_data.get('a', '')

        # --- 1) Probabilités de chaque facteur ---
        prob_pattern = self.get_probabilite_pattern(c1, cX, c2)
        prob_classement = self.get_probabilite_classement(rang_dom, rang_ext)
        prob_force = self.get_probabilite_force(rang_dom, rang_ext, equipe_dom, equipe_ext)
        prob_lieu = self.get_probabilite_lieu_rang(rang_dom, rang_ext)
        prob_forme = contexte.get("prob_forme", {"1": 33.3, "X": 33.3, "2": 33.3})

        # Série de forme
        serie_dom = contexte.get("serie_dom", [])
        serie_ext = contexte.get("serie_ext", [])
        prob_serie_forme = self.get_probabilite_serie_forme(serie_dom, serie_ext)

        # Série de rangs
        evo_dom = contexte.get("evolution_dom", "stable")
        evo_ext = contexte.get("evolution_ext", "stable")
        prob_serie_rang = self.get_probabilite_serie_rang(equipe_dom, equipe_ext, evo_dom, evo_ext)

        # Tendance buts
        bp_dom = contexte.get("bp_moy_dom", 1.5)
        bc_dom = contexte.get("bc_moy_dom", 1.5)
        bp_ext = contexte.get("bp_moy_ext", 1.2)
        bc_ext = contexte.get("bc_moy_ext", 1.2)
        t_adv_dom = contexte.get("type_adv_dom", "medium")
        t_adv_ext = contexte.get("type_adv_ext", "medium")
        prob_tendance = self.get_probabilite_tendance_buts(
            equipe_dom, equipe_ext, bp_dom, bc_dom, bp_ext, bc_ext, t_adv_dom, t_adv_ext
        )

        # --- 2) Fusion pondérée ---
        p = self.poids
        denom = (p["cote_favorite"] + p["forme_recente"] + p["classement"] +
                 p["classement_diff"] + p["zone_vs_zone"] + p["force_lieu"] +
                 p["lieu_rang"] + p["serie_forme"] + p["serie_rang"] +
                 p["tendance_buts"] + p["historique_h2h"])
        if denom == 0:
            denom = 1.0

        def _fuse(key):
            return (
                prob_pattern[key]      * p["cote_favorite"] +
                prob_forme[key]        * p["forme_recente"] +
                prob_classement[key]   * p["classement"] +
                prob_classement[key]   * p["classement_diff"] +  # diff incluse dans classement
                prob_classement[key]   * p["zone_vs_zone"] +     # zone incluse
                prob_force[key]        * p["force_lieu"] +
                prob_lieu[key]         * p["lieu_rang"] +
                prob_serie_forme[key]  * p["serie_forme"] +
                prob_serie_rang[key]   * p["serie_rang"] +
                prob_tendance[key]     * p["tendance_buts"] +
                prob_pattern[key]      * p["historique_h2h"]     # fallback h2h sur cotes
            ) / denom

        final_prob = {
            "1": _fuse("1"),
            "X": _fuse("X"),
            "2": _fuse("2"),
        }

        total = sum(final_prob.values())
        if total > 0:
            final_prob = {k: round(v / total * 100, 1) for k, v in final_prob.items()}

        choix = max(final_prob, key=final_prob.get)

        return {
            "prediction":  choix,
            "probabilites": final_prob,
            "confiance":   final_prob[choix],
            "facteurs":    {
                "pattern_cotes":   prob_pattern,
                "classement":      prob_classement,
                "force":           prob_force,
                "lieu_rang":       prob_lieu,
                "serie_forme":     prob_serie_forme,
                "serie_rang":      prob_serie_rang,
                "tendance_buts":   prob_tendance,
                "forme":           prob_forme,
            },
            "pred_par_facteur": {
                "cote_favorite":   max(prob_pattern, key=prob_pattern.get),
                "classement":      max(prob_classement, key=prob_classement.get),
                "force_lieu":      max(prob_force, key=prob_force.get),
                "serie_forme":     max(prob_serie_forme, key=prob_serie_forme.get),
                "tendance_buts":   max(prob_tendance, key=prob_tendance.get),
                "forme_recente":   max(prob_forme, key=prob_forme.get),
            }
        }

    # ═══════════════════════════════════════════════════════════
    #  STATISTIQUES & RAPPORTS
    # ═══════════════════════════════════════════════════════════

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
        lignes = ["═" * 55, "RAPPORT DES PATTERNS ORACLE V2.3", "═" * 55]
        lignes.append(f"Total matchs appris : {self.stats_globales['total_matchs']}")
        lignes.append(f"Taux réussite : {self.get_stats_apprentissage()['taux_reussite']}%")
        lignes.append("")

        # Cotes larges
        for prefix, label in [("COTES_SERREES", "📊 COTES SERRÉES"),
                               ("FAVORI_FORT", "📊 FAVORI FORT"),
                               ("FAVORI_MODERE", "📊 FAVORI MODÉRÉ"),
                               ("MATCH_OUVERT", "📊 MATCH OUVERT")]:
            if prefix in self.patterns and self.patterns[prefix]["total"] >= 1:
                d = self.patterns[prefix]
                lignes.append(f"{label} ({d['total']} matchs)")
                for r in ["1", "X", "2"]:
                    lignes.append(f"   {r} : {d.get(r,0)/d['total']*100:.1f}%")
                lignes.append("")

        # Zones Z1-Z4
        zones = {k: v for k, v in self.patterns.items() if k.startswith("ZONE_") and isinstance(v, dict) and "total" in v}
        if zones:
            lignes.append("🎯 ZONES Z1-Z4 (Z1:1-5, Z2:6-10, Z3:11-15, Z4:16-20) :")
            for k, v in sorted(zones.items(), key=lambda x: x[1].get("total",0), reverse=True):
                if v["total"] >= 1:
                    best = max(["1","X","2"], key=lambda r: v.get(r,0))
                    lignes.append(f"  {k} ({v['total']}m) → {best} ({v.get(best,0)/v['total']*100:.0f}%)")
            lignes.append("")

        # Force
        forces = {k: v for k, v in self.patterns.items() if k.startswith("FORCE_") and isinstance(v, dict) and "total" in v}
        if forces:
            lignes.append("💪 FORCE DOMICILE vs EXTÉRIEUR (fort/medium/outsider) :")
            for k, v in sorted(forces.items(), key=lambda x: x[1].get("total",0), reverse=True)[:6]:
                if v["total"] >= 1:
                    best = max(["1","X","2"], key=lambda r: v.get(r,0))
                    lignes.append(f"  {k} ({v['total']}m) → {best} ({v.get(best,0)/v['total']*100:.0f}%)")
            lignes.append("")

        # Séries
        series = {k: v for k, v in self.patterns.items() if k.startswith("SERIE_") and isinstance(v, dict) and "total" in v}
        if series:
            lignes.append("🔥 SÉRIES DE VICTOIRES (forme 3 derniers matchs) :")
            for k, v in sorted(series.items(), key=lambda x: x[1].get("total",0), reverse=True)[:8]:
                if v["total"] >= 1:
                    best = max(["1","X","2"], key=lambda r: v.get(r,0))
                    lignes.append(f"  {k} ({v['total']}m) → {best} ({v.get(best,0)/v['total']*100:.0f}%)")
            lignes.append("")

        # Tendances buts
        tends = {k: v for k, v in self.patterns.items() if k.startswith("TEND_") and isinstance(v, dict) and "total" in v}
        if tends:
            lignes.append("⚽ TENDANCES OFFENSIVES/DÉFENSIVES :")
            for k, v in sorted(tends.items(), key=lambda x: x[1].get("total",0), reverse=True)[:8]:
                if v["total"] >= 1:
                    best = max(["1","X","2"], key=lambda r: v.get(r,0))
                    lignes.append(f"  {k} ({v['total']}m) → {best} ({v.get(best,0)/v['total']*100:.0f}%)")
            lignes.append("")

        return "\n".join(lignes)

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

    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()


moteur_apprentissage = MoteurApprentissage()
