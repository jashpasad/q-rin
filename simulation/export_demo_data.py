import json, numpy as np, random
import harvest_debt_sim as M
random.seed(7); np.random.seed(7)
strats = {
 "Q-RIN debt-optimal": M.order_qrin(),
 "Mosca X+Y ranking": M.order_mosca(),
 "Static risk score": M.order_risk_score(),
 "Exposure-first": M.order_exposure_first(),
 "Quick wins first": M.order_quick_wins(),
}
months = list(range(0, 61, 2))
out = {"months": months, "scenarios": list(M.SCENARIOS), "strategies": {}}
for name, od in strats.items():
    fin = M.schedule(od)
    d = {}
    for s in M.SCENARIOS:
        curve = [sum(M.debt_at(j, min(fin[j], t), s) for j in range(M.N)) for t in months]
        d[s] = {"total": M.total_debt(od, s), "curve": curve}
    d["order"] = [{"name": M.items[j]["name"], "cls": M.items[j]["cls"], "kind": M.items[j]["kind"],
                   "start": fin[j]-M.items[j]["effort"], "finish": fin[j]} for j in sorted(fin, key=lambda j: fin[j])]
    out["strategies"][name] = d
rob = json.load(open("robustness.json"))
out["robust_vs_best"] = [round(r["vs_best"]*100, 1) for r in rob]
json.dump(out, open("demo_data.json", "w"))
print({k: round(v["base"]["total"]) for k, v in out["strategies"].items()})
