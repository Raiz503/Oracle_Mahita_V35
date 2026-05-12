"""
╔══════════════════════════════════════════════════════════════════╗
║           CERVEAU ORACLE V3 — Moteur Hybride Amélioré           ║
║  Corrections : momentum LL · Giant Killer ext · terrain dyn.    ║
║  Nouveau     : profil BALANCÉ · apprentissage cross-saisons      ║
║  Philosophie : chaque saison est unique, mais l'histoire enseigne║
╚══════════════════════════════════════════════════════════════════╝
"""
import re
import math


class CerveauOracle:
    def __init__(self):
        # Seuils de décision
        self.seuil_safe = 1.70
        self.seuil_fun  = 3.40

        # ADN des Equipes — profils initiaux (mis à jour dynamiquement par apprendre_profils)
        self.profils = {
            "London Reds":     "VERTICAL",
            "Manchester Blue": "VERTICAL",
            "Liverpool":       "EXPLOSIF",
            "Brentford":       "GIANT_KILLER",
            "Everton":         "LINEAIRE",
            "A. Villa":        "LINEAIRE",
            "Sunderland":      "LANTERNE",
        }
        self.big_four = ["London Reds", "Manchester Blue", "Liverpool", "London Blues"]

        # Poids hybride cote / forme
        self.poids_cote_initial = 0.65
        self.poids_forme_max    = 0.55

        # Dixon-Coles rho
        self.dc_rho = -0.13

        # Avantage terrain de base
        self.avantage_terrain_base = 1.08

        # Memoire cross-saisons : { equipe: { tendance, transitions, historique } }
        self._memoire_cross_saisons = {}

    # ════════════════════════════════════════════════
    #  METHODE PRINCIPALE
    # ════════════════════════════════════════════════

    def analyser_match(self, equipe_dom, equipe_ext, cotes, journee,
                       serie_dom, serie_ext, rang_dom, rang_ext,
                       forme_dom=None, forme_ext=None, h2h=None, ligue=None,
                       match_precedent_dom=None):
        """
        MOTEUR HYBRIDE V3 — Cote + Forme + ADN + H2H + Terrain dynamique + Cross-saisons.
        """
        s_dom = str(serie_dom).upper().strip() if (serie_dom and serie_dom != 0) else ""
        s_ext = str(serie_ext).upper().strip() if (serie_ext and serie_ext != 0) else ""

        nb_matchs = (ligue or {}).get("total_matchs", 0)

        # MODULE 1 : TRAJECTOIRE
        momentum_dom = self._calculer_momentum(s_dom)
        momentum_ext = self._calculer_momentum(s_ext)

        # MODULE 3 : PLAFOND DE VERRE
        plafond_dom = 0.88 if "VVV" in s_dom.replace(" ", "") else 1.0
        plafond_ext = 0.88 if "VVV" in s_ext.replace(" ", "") else 1.0

        # MODULE 2.A : LOI DU RELACHEMENT
        rel_dom = 0.93 if (s_dom.endswith("V") and any(b.upper() in s_dom for b in self.big_four)) else 1.0
        rel_ext = 0.93 if (s_ext.endswith("V") and any(b.upper() in s_ext for b in self.big_four)) else 1.0

        # AVANTAGE TERRAIN DYNAMIQUE
        avantage_terrain = self._avantage_terrain_dynamique(journee, rang_dom, nb_matchs)

        # 1) FORCE COTE
        force_cote_dom = (3.0 / max(cotes[0], 1.01)) * momentum_dom * plafond_dom * rel_dom * avantage_terrain
        force_cote_ext = (3.0 / max(cotes[2], 1.01)) * momentum_ext * plafond_ext * rel_ext

        # 2) FORCE FORME HISTORIQUE
        force_forme_dom, force_forme_ext = self._calculer_force_forme(forme_dom, forme_ext, ligue)

        # 3) FUSION HYBRIDE
        poids_forme = min(self.poids_forme_max, nb_matchs / 100.0)
        poids_cote  = 1.0 - poids_forme
        force_dom = poids_cote * force_cote_dom + poids_forme * force_forme_dom
        force_ext = poids_cote * force_cote_ext + poids_forme * force_forme_ext

        # 4) CORRECTION CROSS-SAISONS
        force_dom, force_ext = self._appliquer_memoire_cross_saisons(equipe_dom, equipe_ext, force_dom, force_ext)

        # 5) H2H
        force_dom, force_ext, h2h_alerte = self._appliquer_h2h(h2h, force_dom, force_ext)

        # 6) ADN DES EQUIPES
        force_dom, force_ext = self._appliquer_adn(equipe_dom, equipe_ext, force_dom, force_ext, rang_dom, rang_ext)

        # 7) POISSON DIXON-COLES
        score_dom, score_ext, prob_score_exact = self._mode_poisson(force_dom, force_ext)

        # ALERTES & CONFIANCE
        alertes = []
        if h2h_alerte:
            alertes.append(h2h_alerte)
        confiance = "MEDIUM"

        # MSS (Survie Critique)
        if journee >= 30:
            if rang_dom >= 17 and cotes[0] > 2.0:
                alertes.append(f"MSS : {equipe_dom} joue sa survie !")
                confiance = "RISQUE"
            if rang_ext >= 17 and cotes[2] > 2.0:
                alertes.append(f"MSS : {equipe_ext} joue sa survie !")
                confiance = "RISQUE"

        # Alerte transition cross-saisons
        for eq in [equipe_dom, equipe_ext]:
            mem = self._memoire_cross_saisons.get(eq, {})
            if mem.get("transitions"):
                last = mem["transitions"][-1]
                if last[0] != last[1]:
                    alertes.append(f"Transition profil {eq} : {last[0]} -> {last[1]}")

        # MODULE 4 : DECISION
        choix = f"Nul ou {equipe_dom}" if cotes[0] < cotes[2] else f"Nul ou {equipe_ext}"
        if cotes[0] < self.seuil_safe or cotes[2] < self.seuil_safe:
            confiance = "BANKER (80-95%)"
            choix = f"{equipe_dom} Gagne" if cotes[0] < cotes[2] else f"{equipe_ext} Gagne"
        elif cotes[1] > self.seuil_fun:
            confiance = "FUN (TICKET)"
            choix = "Match Nul"

        # Bonus convergence
        if (abs(force_cote_dom - force_forme_dom) < 0.3 and
                abs(force_cote_ext - force_forme_ext) < 0.3 and nb_matchs >= 20):
            alertes.append("Convergence Cote+Forme (signal renforce)")
            if "BANKER" in confiance or score_dom != score_ext:
                confiance = "BANKER (80-95%)"

        return {
            "score_predit":     f"{score_dom}:{score_ext}",
            "alertes":          alertes,
            "confiance":        confiance,
            "choix_expert":     choix,
            "force_dom":        round(force_dom, 2),
            "force_ext":        round(force_ext, 2),
            "prob_score_exact": round(prob_score_exact * 100, 1),
            "poids_forme":      round(poids_forme, 2),
            "avantage_terrain": round(avantage_terrain, 3),
        }

    # ════════════════════════════════════════════════
    #  MODULES INTERNES
    # ════════════════════════════════════════════════

    def _calculer_momentum(self, serie):
        """
        CORRECTION V3 : LL (deux defaites) = -15% comme DD.
        VV = +15%, DD = -15%, LL = -15%, reste = neutre.
        """
        clean = serie.replace(" ", "")
        if len(clean) < 2:
            return 1.0
        derniers = clean[-2:]
        if derniers == "VV": return 1.15
        if derniers == "DD": return 0.85
        if derniers == "LL": return 0.85   # CORRECTION : etait absent avant
        return 1.0

    def _avantage_terrain_dynamique(self, journee, rang_dom, nb_matchs):
        """
        NOUVEAU V3 : L'avantage terrain varie selon la situation.
        J30+ equipe relegable : terrain se retourne contre elle (pression) -> +2% seulement.
        Saison mature (50+ matchs) : adversaires connaissent le terrain -> +4%.
        Debut de saison : +8% (base).
        """
        if journee >= 30 and rang_dom >= 17:
            return 1.02
        if nb_matchs >= 50:
            return 1.04
        facteur = max(0.0, 1.0 - nb_matchs / 200.0)
        return 1.04 + (self.avantage_terrain_base - 1.04) * facteur

    def _calculer_force_forme(self, forme_dom, forme_ext, ligue):
        """Modele Poisson : lambda via attaque x defense normalisees."""
        if not forme_dom or not forme_ext or not ligue:
            return 1.4, 1.0
        avg_dom = max(0.1, ligue.get("avg_dom", 1.4))
        avg_ext = max(0.1, ligue.get("avg_ext", 1.1))

        att_dom  = max(0.4, min(2.5, forme_dom["buts_marques_dom"] / avg_dom))
        def_ext  = max(0.4, min(2.5, forme_ext["buts_encaisses_ext"] / avg_dom))
        att_ext  = max(0.4, min(2.5, forme_ext["buts_marques_ext"] / avg_ext))
        def_dom  = max(0.4, min(2.5, forme_dom["buts_encaisses_dom"] / avg_ext))

        return avg_dom * att_dom * def_ext, avg_ext * att_ext * def_dom

    def _appliquer_h2h(self, h2h, f_dom, f_ext):
        """H2H favorable -> +8% pour le favori historique."""
        if not h2h or len(h2h) < 2:
            return f_dom, f_ext, None
        v_dom = sum(1 for (a, b) in h2h if a > b)
        v_ext = sum(1 for (a, b) in h2h if b > a)
        if v_dom >= 2 and v_ext == 0:
            return f_dom * 1.08, f_ext * 0.95, f"H2H favorable domicile ({v_dom}V)"
        if v_ext >= 2 and v_dom == 0:
            return f_dom * 0.95, f_ext * 1.08, f"H2H favorable exterieur ({v_ext}V)"
        return f_dom, f_ext, None

    def _appliquer_adn(self, h, a, f_h, f_a, r_h, r_a):
        """
        Module ADN V3 :
        - GIANT_KILLER : s'applique DOM et EXT contre Big-Four (CORRECTION)
        - LANTERNE : penalise DOM et EXT contre top-10
        - BALANCE (NOUVEAU) : prime de regularite +3%
        """
        ph = self.profils.get(h)
        pa = self.profils.get(a)

        # GIANT_KILLER a domicile
        if ph == "GIANT_KILLER" and any(b in a for b in self.big_four):
            f_h *= 1.15
        # GIANT_KILLER en deplacement (CORRECTION V3)
        if pa == "GIANT_KILLER" and any(b in h for b in self.big_four):
            f_a *= 1.10

        # LANTERNE penalise contre top-10
        if pa == "LANTERNE" and r_h < 10:
            f_a *= 0.80
        if ph == "LANTERNE" and r_a < 10:
            f_h *= 0.80

        # BALANCE : regularite (NOUVEAU)
        if ph == "BALANCE":
            f_h *= 1.03
        if pa == "BALANCE":
            f_a *= 1.03

        return f_h, f_a

    def _appliquer_memoire_cross_saisons(self, equipe_dom, equipe_ext, f_dom, f_ext):
        """
        NOUVEAU V3 : Ajustement base sur la trajectoire inter-saisons.
        Une equipe qui progresse entre saisons voit sa force augmenter.
        """
        for eq, is_dom in [(equipe_dom, True), (equipe_ext, False)]:
            mem = self._memoire_cross_saisons.get(eq)
            if not mem:
                continue
            tendance = mem.get("tendance", 0.0)
            facteur  = 1.0 + max(-0.10, min(0.10, tendance * 0.05))
            if is_dom:
                f_dom *= facteur
            else:
                f_ext *= facteur
        return f_dom, f_ext

    # ════════════════════════════════════════════════
    #  POISSON & DIXON-COLES
    # ════════════════════════════════════════════════

    def _mode_poisson(self, lambda_dom, lambda_ext):
        lambda_dom = max(0.1, lambda_dom)
        lambda_ext = max(0.1, lambda_ext)
        best = (0, 0, 0.0)
        for h in range(7):
            p_h = self._poisson(lambda_dom, h)
            for a in range(7):
                p_a = self._poisson(lambda_ext, a)
                p   = self._tau_dixon_coles(h, a, lambda_dom, lambda_ext) * p_h * p_a
                if p > best[2]:
                    best = (h, a, p)
        return best[0], best[1], best[2]

    def _tau_dixon_coles(self, x, y, lam, mu):
        rho = self.dc_rho
        if x == 0 and y == 0: return 1.0 - lam * mu * rho
        if x == 0 and y == 1: return 1.0 + lam * rho
        if x == 1 and y == 0: return 1.0 + mu  * rho
        if x == 1 and y == 1: return 1.0 - rho
        return 1.0

    def probabilites_1n2_dixon_coles(self, lambda_dom, lambda_ext):
        lambda_dom = max(0.1, lambda_dom)
        lambda_ext = max(0.1, lambda_ext)
        p_1 = p_n = p_2 = 0.0
        for h in range(7):
            p_h = self._poisson(lambda_dom, h)
            for a in range(7):
                p_a = self._poisson(lambda_ext, a)
                p   = self._tau_dixon_coles(h, a, lambda_dom, lambda_ext) * p_h * p_a
                if h > a:    p_1 += p
                elif h == a: p_n += p
                else:        p_2 += p
        total = p_1 + p_n + p_2
        if total > 0:
            p_1, p_n, p_2 = p_1/total, p_n/total, p_2/total
        return p_1, p_n, p_2

    @staticmethod
    def _poisson(lam, k):
        if lam <= 0:
            return 1.0 if k == 0 else 0.0
        return (math.exp(-lam) * lam ** k) / math.factorial(k)

    # ════════════════════════════════════════════════
    #  APPRENTISSAGE PROFILS (intra-saison)
    # ════════════════════════════════════════════════

    def apprendre_profils(self, historique_saison, teams_list):
        """
        Apprentissage auto des profils depuis les resultats d'une saison.
        Profils : GIANT_KILLER · LANTERNE · VERTICAL · EXPLOSIF · LINEAIRE · BALANCE (nouveau)
        """
        if not historique_saison:
            return {"profils_appris": {}, "rapport": "Aucun historique disponible."}

        stats = {t: {"buts_marques": [], "vs_big4": [], "vs_top10": []} for t in teams_list}

        # Classement temporaire pour identifier top-10
        cl = {t: 0 for t in teams_list}
        for jk, data in historique_saison.items():
            for m in data.get("res", []):
                try:
                    sh, sa = map(int, m['s'].replace('-', ':').split(':'))
                    if sh > sa:   cl[m['h']] = cl.get(m['h'], 0) + 3
                    elif sa > sh: cl[m['a']] = cl.get(m['a'], 0) + 3
                    else:
                        cl[m['h']] = cl.get(m['h'], 0) + 1
                        cl[m['a']] = cl.get(m['a'], 0) + 1
                except: continue
        top10 = set(sorted(cl, key=cl.get, reverse=True)[:10])

        for jk, data in historique_saison.items():
            for m in data.get("res", []):
                try:
                    sh, sa = map(int, m['s'].replace('-', ':').split(':'))
                    h, a = m['h'], m['a']
                    if h in stats:
                        stats[h]["buts_marques"].append(sh)
                        if a in self.big_four: stats[h]["vs_big4"].append(1 if sh > sa else 0)
                        if a in top10:         stats[h]["vs_top10"].append(1 if sh < sa else 0)
                    if a in stats:
                        stats[a]["buts_marques"].append(sa)
                        if h in self.big_four: stats[a]["vs_big4"].append(1 if sa > sh else 0)
                        if h in top10:         stats[a]["vs_top10"].append(1 if sa < sh else 0)
                except: continue

        nouveaux = {}
        rapport  = []
        for t in teams_list:
            s    = stats[t]
            buts = s["buts_marques"]
            if len(buts) < 5: continue
            moy = sum(buts) / len(buts)
            var = sum((b - moy)**2 for b in buts) / len(buts)

            profil = None
            if len(s["vs_big4"]) >= 2 and sum(s["vs_big4"]) / len(s["vs_big4"]) >= 0.40:
                profil = "GIANT_KILLER"
            elif len(s["vs_top10"]) >= 4 and sum(s["vs_top10"]) / len(s["vs_top10"]) >= 0.75:
                profil = "LANTERNE"
            elif moy >= 1.8:
                profil = "VERTICAL"
            elif var >= 1.5:
                profil = "EXPLOSIF"
            elif var <= 0.35:
                profil = "LINEAIRE"
            elif var <= 0.6 or (0.6 < var < 1.0 and 1.2 <= moy <= 1.7):
                profil = "BALANCE"   # NOUVEAU : stable et regulier

            if profil:
                ancien = self.profils.get(t)
                nouveaux[t] = profil
                if ancien != profil:
                    rapport.append(f"  {t} : {ancien or '-'} -> {profil} (moy={moy:.2f}, var={var:.2f})")

        self.profils.update(nouveaux)
        return {
            "profils_appris": nouveaux,
            "nb_changements": len(rapport),
            "rapport": "\n".join(rapport) if rapport else "Profils deja a jour.",
        }

    # ════════════════════════════════════════════════
    #  APPRENTISSAGE CROSS-SAISONS (NOUVEAU V3)
    # ════════════════════════════════════════════════

    def apprendre_cross_saisons(self, historique_complet):
        """
        NOUVEAU V3 — Analyse TOUTES les saisons pour detecter les trajectoires
        d'equipes entre saisons.

        Philosophie : une equipe faible peut devenir forte.
        Chaque saison est unique, mais l'histoire inter-saisons enseigne.
        """
        if not historique_complet or len(historique_complet) < 2:
            return {"rapport": "Pas assez de saisons pour l'analyse cross-saisons."}

        saisons = sorted(
            historique_complet.keys(),
            key=lambda s: re.search(r'\d+', s).group() if re.search(r'\d+', s) else s
        )

        # Performances par saison par equipe (pts/match)
        perfs = {}
        for saison in saisons:
            pts_eq = {}
            mj_eq  = {}
            for jk, data in historique_complet[saison].items():
                for m in data.get("res", []):
                    try:
                        sh, sa = map(int, m['s'].replace('-', ':').split(':'))
                        h, a = m['h'], m['a']
                        pts_eq[h] = pts_eq.get(h, 0) + (3 if sh > sa else (1 if sh == sa else 0))
                        pts_eq[a] = pts_eq.get(a, 0) + (3 if sa > sh else (1 if sh == sa else 0))
                        mj_eq[h]  = mj_eq.get(h, 0) + 1
                        mj_eq[a]  = mj_eq.get(a, 0) + 1
                    except: continue
            perfs[saison] = {eq: pts_eq[eq] / mj_eq[eq] for eq in pts_eq if mj_eq.get(eq, 0) >= 5}

        # Tendances inter-saisons
        toutes_eq = set()
        for p in perfs.values(): toutes_eq.update(p.keys())

        rapport = []
        for eq in toutes_eq:
            vals = [(s, perfs[s][eq]) for s in saisons if eq in perfs.get(s, {})]
            if len(vals) < 2: continue

            tendance = vals[-1][1] - vals[0][1]

            if eq not in self._memoire_cross_saisons:
                self._memoire_cross_saisons[eq] = {"tendance": 0.0, "transitions": [], "historique": []}
            self._memoire_cross_saisons[eq]["tendance"]  = tendance
            self._memoire_cross_saisons[eq]["historique"] = vals

            if abs(tendance) >= 0.5:
                emoji = "MONTEE" if tendance > 0 else "DECLIN"
                rapport.append(
                    f"  {emoji} | {eq} : {tendance:+.2f} pts/match "
                    f"({vals[0][0]} -> {vals[-1][0]}) · profil: {self.profils.get(eq, '?')}"
                )

        return {
            "nb_equipes_analysees": len(toutes_eq),
            "nb_saisons":           len(saisons),
            "rapport": "\n".join(rapport) if rapport else "Aucune trajectoire significative.",
            "memoire": {
                eq: {"tendance": round(v["tendance"], 3), "nb_saisons": len(v["historique"])}
                for eq, v in self._memoire_cross_saisons.items()
            }
        }

    # ════════════════════════════════════════════════
    #  BACKTESTING
    # ════════════════════════════════════════════════

    def backtester(self, historique_saison, helpers=None):
        """Re-predit chaque journee avec uniquement les donnees anterieures."""
        rapport = {"journees": [], "rating_global": 0, "scores_exacts": 0,
                   "tendance_1n2": 0, "total": 0, "evolution": []}
        keys = sorted(
            [k for k in historique_saison.keys() if re.search(r'\d+', k)],
            key=lambda k: int(re.search(r'\d+', k).group())
        )
        if not keys: return rapport

        cumul_pts = cumul_total = 0
        for i, jk in enumerate(keys):
            data = historique_saison[jk]
            cal, res = data.get("cal", []), data.get("res", [])
            if not cal or not res: continue

            sous_hist = {kk: historique_saison[kk] for kk in keys[:i]}
            j_num = int(re.search(r'\d+', jk).group())

            series = formes = ligue_stats = None
            if helpers:
                series      = helpers["get_series"](sous_hist, helpers["teams_list"], 5)
                formes_full = helpers["get_team_form_stats"](sous_hist, helpers["teams_list"])
                ligue_stats = formes_full.pop("__ligue__", None)
                formes      = formes_full

            j_pts = j_exacts = j_tend = j_total = 0
            for cal_m, res_m in zip(cal, res):
                if cal_m['h'] != res_m['h'] or cal_m['a'] != res_m['a']: continue
                pred = self.analyser_match(
                    equipe_dom=cal_m['h'], equipe_ext=cal_m['a'], cotes=cal_m['o'],
                    journee=j_num, serie_dom=(series or {}).get(cal_m['h'], 0),
                    serie_ext=(series or {}).get(cal_m['a'], 0),
                    rang_dom=10, rang_ext=10,
                    forme_dom=(formes or {}).get(cal_m['h']),
                    forme_ext=(formes or {}).get(cal_m['a']),
                    h2h=helpers["get_h2h"](sous_hist, cal_m['h'], cal_m['a'], 3) if helpers else None,
                    ligue=ligue_stats
                )
                try:
                    srh, sra = map(int, res_m['s'].replace('-', ':').split(':'))
                    sph, spa = map(int, pred['score_predit'].split(':'))
                    j_total += 1
                    if srh == sph and sra == spa: j_pts += 3; j_exacts += 1
                    tr = 1 if srh > sra else (2 if sra > srh else 0)
                    tp = 1 if sph > spa else (2 if spa > sph else 0)
                    if tr == tp and not (srh == sph and sra == spa): j_pts += 1; j_tend += 1
                    elif tr == tp: j_tend += 1
                except: continue

            cumul_pts += j_pts; cumul_total += j_total
            rapport["journees"].append({"journee": jk, "matchs": j_total, "exacts": j_exacts,
                "tendance_1n2": j_tend, "pts": j_pts,
                "rating": (j_pts / (j_total * 3) * 100) if j_total else 0})
            rapport["evolution"].append({"journee": j_num,
                "rating_cumule": (cumul_pts / (cumul_total * 3) * 100) if cumul_total else 0})
            rapport["scores_exacts"] += j_exacts
            rapport["tendance_1n2"]  += j_tend
            rapport["total"]         += j_total

        rapport["rating_global"] = (cumul_pts / (cumul_total * 3) * 100) if cumul_total else 0
        return rapport

    # ════════════════════════════════════════════════
    #  AUTO-CALIBRATION & PERFORMANCE
    # ════════════════════════════════════════════════

    def auto_calibrer(self, historique_saison):
        rapport = {"ajustements": [], "performance_avant": 0, "biais_detecte": None}
        if not historique_saison: return rapport

        sur_dom = sur_ext = total = 0
        for jk, data in historique_saison.items():
            for r, p in zip(data.get("res", []), data.get("pro", [])):
                try:
                    srh, sra = map(int, r['s'].replace('-', ':').split(':'))
                    sp = p.get('score_predit') or re.search(r"(\d+):(\d+)", p.get('m', '')).group(0)
                    sph, spa = map(int, sp.split(':'))
                    if sph > srh: sur_dom += 1
                    if spa > sra: sur_ext += 1
                    total += 1
                except: continue

        if total >= 10:
            if sur_dom / total > 0.55:
                rapport["biais_detecte"] = "Sur-evaluation domicile"
                rapport["ajustements"].append("Reduction force domicile 5%")
            elif sur_ext / total > 0.55:
                rapport["biais_detecte"] = "Sur-evaluation exterieur"
                rapport["ajustements"].append("Reduction force exterieur 5%")

        perf = self.calculer_performance_globale(historique_saison)
        rapport["performance_avant"] = perf["rating_general"]
        if perf["rating_general"] < 60 and perf["total_matchs"] >= 10:
            self.seuil_safe = max(1.50, self.seuil_safe - 0.10)
            rapport["ajustements"].append(f"Seuil BANKER abaisse a {self.seuil_safe:.2f}")
        elif perf["rating_general"] > 85 and perf["total_matchs"] >= 10:
            self.seuil_safe = min(2.00, self.seuil_safe + 0.05)
            rapport["ajustements"].append(f"Seuil BANKER releve a {self.seuil_safe:.2f}")

        return rapport

    def calculer_performance_globale(self, historique_saison):
        stats = {"total": 0, "1n2": 0, "exacts": 0, "pts": 0}
        if not historique_saison: return self._vident()
        for jk, data in historique_saison.items():
            for r, p in zip(data.get("res", []), data.get("pro", [])):
                stats["total"] += 1
                try:
                    srh, sra = map(int, r['s'].replace('-', ':').split(':'))
                    m = re.search(r"(\d+):(\d+)", p['m'])
                    if not m: continue
                    sph, spa = map(int, m.groups())
                    if srh == sph and sra == spa: stats["exacts"] += 1; stats["pts"] += 3
                    tr = 1 if srh > sra else 2 if sra > srh else 0
                    tp = 1 if sph > spa else 2 if spa > sph else 0
                    if tr == tp: stats["1n2"] += 1; stats["pts"] += 1
                except: continue
        t = stats["total"] or 1
        return {"total_matchs": stats["total"], "taux_1n2": stats["1n2"]/t*100,
                "scores_exacts": stats["exacts"], "points_oracle": stats["pts"],
                "moyenne_points": stats["pts"]/t, "rating_general": min(100, stats["pts"]/(t*3)*100)}

    def _vident(self):
        return {"total_matchs": 0, "taux_1n2": 0, "scores_exacts": 0,
                "points_oracle": 0, "moyenne_points": 0, "rating_general": 0}


# Instance globale exportee
cerveau1 = CerveauOracle()
