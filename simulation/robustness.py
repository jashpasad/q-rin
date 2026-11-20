"""Robustness check: re-draw every synthetic parameter for many random banks and
measure how much debt-optimal ordering saves versus the best standard heuristic."""
import random, copy, json
import numpy as np
import harvest_debt_sim as M

random.seed(11); np.random.seed(11)
ORIG = copy.deepcopy(M.items)
BANKS = 120
out = []
for b in range(BANKS):
    for i, it in enumerate(M.items):
        o = ORIG[i]
        it["effort"] = max(1, round(o["effort"] * np.random.uniform(0.5, 1.5)))
        if o["kind"] != "prereq":
            vol_mult = np.exp(np.random.uniform(np.log(1/3), np.log(3)))
            val_mult = np.exp(np.random.uniform(np.log(1/2), np.log(2)))
            h = min(0.95, max(0.001, o["h"] * np.random.uniform(0.5, 1.5)))
            it["h"] = h
            it["v"] = o["v"] * val_mult
            it["r"] = o["r"] / o["h"] * h * vol_mult * val_mult
    M.TABLE = {sc: np.array([M.cum_debt_table(it, sc) for it in M.items]) for sc in M.SCENARIOS}
    q = M.expected_debt(M.order_qrin(iters=2500))
    base = {
        "mosca": M.expected_debt(M.order_mosca()),
        "exposure": M.expected_debt(M.order_exposure_first()),
        "risk": M.expected_debt(M.order_risk_score()),
        "quick": M.expected_debt(M.order_quick_wins()),
    }
    best_h = min(base.values())
    out.append(dict(vs_best=1 - q / best_h, vs_mosca=1 - q / base["mosca"],
                    vs_risk=1 - q / base["risk"]))

for k in ["vs_best", "vs_mosca", "vs_risk"]:
    a = np.array([o[k] for o in out]) * 100
    print(f"{k:9s} median {np.median(a):5.1f}%  IQR {np.percentile(a,25):5.1f}-{np.percentile(a,75):5.1f}%  min {a.min():5.1f}%")
json.dump(out, open("robustness.json", "w"))
