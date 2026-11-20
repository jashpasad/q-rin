import json, random, numpy as np
import harvest_debt_sim as M
random.seed(7); np.random.seed(7)
out = {}
q = M.order_qrin(); mo = M.order_mosca(); rk = M.order_risk_score()

# 1. cost of delay (start migration d months later)
def debt_shift(order, d, sc):
    fin = M.schedule(order)
    return sum(M.debt_at(j, min(fin[j]+d, 240), sc) for j in range(M.N))
def exp_shift(order, d):
    return sum(M.SCENARIOS[s]["weight"]*debt_shift(order, d, s) for s in M.SCENARIOS)
delays = [0,3,6,12,18,24,36]
out["delay"] = {"months": delays,
  "qrin": [exp_shift(q,d) for d in delays],
  "mosca": [exp_shift(mo,d) for d in delays]}

# 2. team sensitivity
teams = [2,3,4,6,8]; ts = {"teams":teams,"qrin":[],"mosca":[],"risk":[],"makespan":[]}
for T in teams:
    M.TEAMS = T
    oq = M.order_qrin(iters=3000)
    ts["qrin"].append(M.expected_debt(oq)); ts["mosca"].append(M.expected_debt(M.order_mosca()))
    ts["risk"].append(M.expected_debt(M.order_risk_score()))
    ts["makespan"].append(max(M.schedule(oq).values())/12)
M.TEAMS = 4
out["teams"] = ts

# 3. debt by data class (base)
def by_class(order, sc="base"):
    fin = M.schedule(order); d = {}
    for j in range(M.N):
        c = M.items[j]["cls"]; d[c] = d.get(c,0)+M.debt_at(j, fin[j], sc)
    return d
out["by_class"] = {"qrin": by_class(q), "mosca": by_class(mo), "risk": by_class(rk)}

# 4. pareto: share of unmitigated 4-yr debt by system
contrib = sorted([(M.items[j]["name"], M.debt_at(j, 48, "base")) for j in range(M.N) if M.items[j]["r"]>0], key=lambda x:-x[1])
tot = sum(c for _,c in contrib)
out["pareto"] = [{"name":n,"share":c/tot} for n,c in contrib]

# 5. archives-last variant of Q-RIN
qa = [j for j in q if M.items[j]["kind"]!="archive"] + [j for j in q if M.items[j]["kind"]=="archive"]
out["archives"] = {"qrin": M.expected_debt(q), "qrin_archives_last": M.expected_debt(qa)}

# 6. CRQC CDFs
yrs = list(np.round(np.arange(0,30.5,0.5),2))
out["cdf"] = {"years": yrs, **{s: [float(M.F(y, s)) for y in yrs] for s in M.SCENARIOS}}

# 7. ledger
fin = M.schedule(q); w = []
for j,it in enumerate(M.items):
    rate0 = sum(M.SCENARIOS[s]["weight"]*it["r"]*M.F(it["L"], s) for s in M.SCENARIOS)
    w.append(dict(name=it["name"], cls=it["cls"], kind=it["kind"], L=it["L"], effort=it["effort"],
                  rate=rate0, ratio=rate0/it["effort"], finish=fin[j], preds=it["preds"]))
out["ledger"] = sorted(w, key=lambda x: x["finish"])

# 8. robustness vs each baseline
rob = json.load(open("robustness.json"))
out["rob"] = {k:[round(r[k]*100,1) for r in rob] for k in ["vs_best","vs_mosca","vs_risk"]}
json.dump(out, open("more_data.json","w"))
print("delay", [round(x/1e6,3) for x in out["delay"]["qrin"]], [round(x/1e6,3) for x in out["delay"]["mosca"]])
print("teams", [round(x/1e6,2) for x in ts["qrin"]], [round(x/1e6,2) for x in ts["mosca"]], [round(x,1) for x in ts["makespan"]])
print("class q", {k:round(v/1e3) for k,v in out["by_class"]["qrin"].items()})
print("class m", {k:round(v/1e3) for k,v in out["by_class"]["mosca"].items()})
cum=0
for i,p in enumerate(out["pareto"]):
    cum+=p["share"]
    if i in (2,4,6,9): print("top",i+1,round(cum*100,1))
print("archives", {k:round(v/1e6,3) for k,v in out["archives"].items()})
