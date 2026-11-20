"""
Q-RIN preliminary simulation: does migration ORDER change cumulative
harvest-now-decrypt-later (HNDL) exposure ("harvest debt")?

Model
-----
Each system j (a data flow or a stored-ciphertext archive) accrues harvest debt
until its quantum-vulnerable key establishment / key wrapping is replaced
(completion time C_j, in months):

    D_j = integral_0^{C_j}  r_j * F( t/12 + L_j )  dt

  r_j : value-weighted harvestable volume per month
        flows    : records/month x value/record x P(path is harvested)
        archives : stored records x value/record x P(archive stolen per month)
  L_j : secrecy lifetime of the data class, in years
  F   : CDF of the arrival time (in years from now) of a cryptographically
        relevant quantum computer (CRQC). Data captured at time t is lost
        if a CRQC arrives before t + L_j.

Total harvest debt = sum_j D_j. Minimising it over migration orders, with
parallel teams and precedence constraints, is a weighted-completion-time
scheduling problem (Smith's rule is optimal for one team with no
precedence and constant weights).

All parameters are SYNTHETIC and illustrative: a stylised mid-size Indian
bank built from public specifications. Results show the size of the
ordering effect, not a forecast for any real institution.
"""
import math
import random
import json
import numpy as np
from scipy.stats import lognorm

random.seed(7)
np.random.seed(7)

# ---------------------------------------------------------------- CRQC scenarios
# Lognormal arrival time in years from now (late 2026).
# base: calibrated loosely to GRI/evolutionQ 2025 expert survey
#       (P(<=10y) ~ 0.33, P(<=20y) ~ 0.76)
SCENARIOS = {
    "aggressive":   dict(median=4.5, sigma=0.5, weight=0.25),  # ~2031
    "base":         dict(median=13.0, sigma=0.6, weight=0.50),  # ~2039
    "conservative": dict(median=22.0, sigma=0.6, weight=0.25),  # ~2048
}
def F(years, sc):
    p = SCENARIOS[sc]
    return lognorm.cdf(years, s=p["sigma"], scale=p["median"])

# ---------------------------------------------------------------- data classes
# class: (secrecy lifetime L in years, value units per record)
CLASSES = {
    "BIO":   (60.0, 50.0),   # biometric identity data: cannot be changed
    "CRED":  (3.0, 20.0),    # PINs / long-lived credentials until reset
    "KYC":   (15.0, 10.0),   # identity documents, PII, account linkage
    "CARD":  (3.0, 8.0),     # card data until reissue
    "PAY":   (7.0, 1.0),     # payment messages / financial behaviour
    "TRADE": (0.08, 3.0),    # orders and positions: value decays in weeks
    "TREAS": (3.0, 500.0),   # treasury, M&A, board communications
    "INT":   (3.0, 0.5),     # internal staff traffic
}

# ---------------------------------------------------------------- synthetic bank
# (name, class, kind, volume_k (per month or stock), harvest prob (per path
#  or per month for archives), effort team-months, internet_facing, preds, value override)
S = [
 ("Internet banking web TLS",        "PAY",  "flow", 3000,  0.9, 2,  1, [], None),
 ("Mobile banking API",              "PAY",  "flow", 5000,  0.9, 4,  1, [], None),
 ("UPI credential blocks (RSA-2048)","CRED", "flow", 20000, 0.4, 14, 0, ["HSM PQC upgrade"], None),
 ("AePS biometric PID path",         "BIO",  "flow", 800,   0.5, 14, 0, ["HSM PQC upgrade"], None),
 ("CKYC/eKYC uploads (SFTP+PGP)",    "KYC",  "flow", 200,   0.6, 5,  1, [], None),
 ("Card data to networks",           "CARD", "flow", 4000,  0.6, 7,  0, [], None),
 ("Payment gateway merchant API",    "CARD", "flow", 3000,  0.9, 4,  1, [], None),
 ("SWIFT cross-border messaging",    "PAY",  "flow", 60,    0.8, 10, 1, ["Enterprise PKI hybrid CA"], 30.0),
 ("SFMS / RTGS / NEFT",              "PAY",  "flow", 2000,  0.3, 12, 0, ["Enterprise PKI hybrid CA"], None),
 ("NACH host-to-host files",         "PAY",  "flow", 6000,  0.4, 8,  0, [], None),
 ("Corporate H2H salary files (PGP)","KYC",  "flow", 500,   0.6, 5,  1, [], None),
 ("Treasury dealing / FX",           "TRADE","flow", 300,   0.5, 3,  0, [], None),
 ("IFSC exchange order flow",        "TRADE","flow", 1000,  0.4, 5,  0, [], None),
 ("Board and M&A email",             "TREAS","flow", 2,     0.7, 2,  1, [], None),
 ("Credit bureau API",               "KYC",  "flow", 400,   0.6, 4,  1, [], None),
 ("Loan docs with DSA partners",     "KYC",  "flow", 150,   0.7, 4,  1, [], None),
 ("Wealth / PMS client portal",      "KYC",  "flow", 100,   0.9, 3,  1, [], 12.0),
 ("Bancassurance partner API",       "KYC",  "flow", 80,    0.6, 3,  1, [], None),
 ("Inter-DC replication (IPsec)",    "KYC",  "flow", 30000, 0.15,5,  0, [], None),
 ("DR site link",                    "KYC",  "flow", 20000, 0.15,4,  0, [], None),
 ("Core banking to branch WAN",      "PAY",  "flow", 8000,  0.2, 10, 0, ["Enterprise PKI hybrid CA"], None),
 ("CRM / call-centre SaaS",          "KYC",  "flow", 600,   0.8, 3,  1, [], None),
 ("Data-lake export to cloud",       "KYC",  "flow", 10000, 0.3, 3,  1, [], None),
 ("Staff remote VPN",                "INT",  "flow", 2000,  0.8, 2,  1, [], None),
 ("ATM host network",                "CARD", "flow", 1500,  0.4, 12, 0, ["HSM PQC upgrade"], None),
 ("Regulatory reporting (STR, CIMS)","KYC",  "flow", 20,    0.5, 3,  1, [], 15.0),
 ("Aadhaar data vault / tokeniser",  "KYC",  "flow", 500,   0.15,5,  0, ["HSM PQC upgrade"], None),
 # stored ciphertext wrapped with RSA/ECC (harvest = future breach of the store)
 ("PGP file archive (7 yrs)",        "KYC",  "archive", 50000,  0.005, 3, 0, ["KMS PQC key-wrap"], None),
 ("Payment logs w/ RSA-wrapped creds","CRED","archive", 200000, 0.003, 4, 0, ["KMS PQC key-wrap"], None),
 ("Backups with RSA-wrapped DEKs",   "KYC",  "archive", 100000, 0.004, 4, 0, ["KMS PQC key-wrap"], None),
 ("S/MIME email archive",            "TREAS","archive", 5,      0.005, 2, 0, ["KMS PQC key-wrap"], None),
 ("Auth logs retaining encrypted payloads","BIO","archive",2000,0.003, 3, 0, ["KMS PQC key-wrap"], None),
 # enabling prerequisites: accrue no debt themselves but gate others
 ("HSM PQC upgrade",                 "INT",  "prereq", 0, 0, 6, 0, [], None),
 ("Enterprise PKI hybrid CA",        "INT",  "prereq", 0, 0, 6, 0, [], None),
 ("KMS PQC key-wrap",                "INT",  "prereq", 0, 0, 3, 0, [], None),
]

items = []
for (name, cls, kind, vol, h, eff, inet, preds, vov) in S:
    L, v = CLASSES[cls]
    if vov is not None:
        v = vov
    r = 0.0 if kind == "prereq" else vol * v * h      # units per month
    items.append(dict(name=name, cls=cls, kind=kind, L=L, v=v, r=r, h=h,
                      effort=eff, inet=inet, preds=preds))
IDX = {it["name"]: i for i, it in enumerate(items)}
N = len(items)
TEAMS = 4

# precompute debt integral tables on a monthly grid (up to 20 years)
GRID = np.arange(0, 241)
def cum_debt_table(it, sc):
    if it["r"] == 0:
        return np.zeros(len(GRID))
    rate = it["r"] * F(GRID / 12.0 + it["L"], sc)
    # trapezoid cumulative integral
    c = np.concatenate([[0.0], np.cumsum((rate[1:] + rate[:-1]) / 2.0)])
    return c
TABLE = {sc: np.array([cum_debt_table(it, sc) for it in items]) for sc in SCENARIOS}

def debt_at(j, C, sc):
    tab = TABLE[sc][j]
    lo = int(math.floor(C)); hi = min(lo + 1, len(GRID) - 1)
    frac = C - lo
    return tab[lo] * (1 - frac) + tab[hi] * frac

# ---------------------------------------------------------------- list scheduler
def schedule(order):
    """Parallel list scheduling with precedence: whenever a team frees up,
    start the highest-priority item whose predecessors are complete."""
    finish = {}
    team_free = [0.0] * TEAMS
    remaining = list(order)
    t_now = 0.0
    running = []  # (finish_time, j)
    while remaining:
        team_free.sort()
        t_now = max(t_now, team_free[0])
        # find first available by priority
        chosen = None
        for j in remaining:
            ok = True
            for p in items[j]["preds"]:
                pj = IDX[p]
                if pj not in finish or finish[pj] > t_now + 1e-9:
                    ok = False; break
            if ok:
                chosen = j; break
        if chosen is None:
            # wait until the next predecessor finishes
            future = [f for f in finish.values() if f > t_now + 1e-9]
            t_now = min(future)
            team_free[0] = max(team_free[0], t_now)
            continue
        start = max(team_free[0], t_now)
        end = start + items[chosen]["effort"]
        finish[chosen] = end
        team_free[0] = end
        remaining.remove(chosen)
    return finish

def total_debt(order, sc):
    fin = schedule(order)
    return sum(debt_at(j, fin[j], sc) for j in range(N))

def expected_debt(order):
    return sum(SCENARIOS[s]["weight"] * total_debt(order, s) for s in SCENARIOS)

# ---------------------------------------------------------------- orderings
def mean_F_window(L, years=4.0):
    ts = np.linspace(0, years, 25)
    return sum(SCENARIOS[s]["weight"] * np.mean(F(ts + L, s)) for s in SCENARIOS)

def order_qrin(objective=expected_debt, iters=6000):
    # seed: Smith-style ratio; prerequisites inherit their dependants' weight
    w = np.array([it["r"] * mean_F_window(it["L"]) for it in items])
    for i, it in enumerate(items):
        if it["kind"] == "prereq":
            deps = [j for j, jt in enumerate(items) if it["name"] in jt["preds"]]
            w[i] = sum(w[j] for j in deps)
    ratio = [w[i] / items[i]["effort"] for i in range(N)]
    order = sorted(range(N), key=lambda i: -ratio[i])
    best = objective(order)
    # local search: random swaps and insertions
    for _ in range(iters):
        cand = order[:]
        a, b = random.sample(range(N), 2)
        if random.random() < 0.5:
            cand[a], cand[b] = cand[b], cand[a]
        else:
            x = cand.pop(a); cand.insert(b, x)
        val = objective(cand)
        if val < best:
            best, order = val, cand
    return order

def order_mosca():
    # largest (shelf-life X + migration time Y) first, a common heuristic
    return sorted(range(N), key=lambda i: -(items[i]["L"] + items[i]["effort"] / 12.0))

def order_exposure_first():
    # internet-facing first, then by data sensitivity
    return sorted(range(N), key=lambda i: (-items[i]["inet"], -items[i]["v"]))

def order_risk_score():
    # static risk score: sensitivity x exposure x timeline (ignores volume/effort)
    def score(i):
        it = items[i]
        timeline = min(it["L"] / 10.0, 1.0)
        return it["v"] * max(it["h"], 0.1) * timeline
    return sorted(range(N), key=lambda i: -score(i))

def order_quick_wins():
    return sorted(range(N), key=lambda i: items[i]["effort"])

def random_orders(k=300):
    return [random.sample(range(N), N) for _ in range(k)]

# ---------------------------------------------------------------- run
if __name__ == "__main__":
    strategies = {
        "Q-RIN debt-optimal": order_qrin(),
        "Mosca X+Y ranking": order_mosca(),
        "Exposure-first": order_exposure_first(),
        "Static risk score": order_risk_score(),
        "Quick wins first": order_quick_wins(),
    }
    res = {}
    for name, od in strategies.items():
        res[name] = {s: total_debt(od, s) for s in SCENARIOS}
        res[name]["expected"] = expected_debt(od)
    rnd = random_orders()
    res["Random (mean of 300)"] = {
        s: float(np.mean([total_debt(o, s) for o in rnd])) for s in SCENARIOS}
    res["Random (mean of 300)"]["expected"] = float(np.mean([expected_debt(o) for o in rnd]))

    # per-scenario optimum (for regret)
    opt = {}
    for s in SCENARIOS:
        o = order_qrin(objective=lambda od, s=s: total_debt(od, s), iters=4000)
        opt[s] = total_debt(o, s)

    base = res["Q-RIN debt-optimal"]
    print(f"{'strategy':28s} {'aggr':>10s} {'base':>10s} {'cons':>10s} {'expected':>10s}  vs Q-RIN")
    for name, r in res.items():
        print(f"{name:28s} {r['aggressive']:10.3e} {r['base']:10.3e} {r['conservative']:10.3e} {r['expected']:10.3e}  "
              f"{(r['expected']/base['expected']-1)*100:+6.1f}%")
    print("\nQ-RIN regret vs per-scenario optimum:")
    for s in SCENARIOS:
        print(f"  {s:12s} {(base[s]/opt[s]-1)*100:5.2f}%")
    print("\nDebt reduction of Q-RIN vs each baseline (expected):")
    for name, r in res.items():
        if name != "Q-RIN debt-optimal":
            print(f"  {name:28s} {(1-base['expected']/r['expected'])*100:5.1f}%")

    fin = schedule(strategies["Q-RIN debt-optimal"])
    print(f"\nMakespan (all systems migrated): {max(fin.values())/12:.1f} years with {TEAMS} teams")
    print("\nQ-RIN migration order (first 12):")
    for j in sorted(fin, key=lambda j: fin[j])[:12]:
        print(f"  finish {fin[j]:5.1f} mo  {items[j]['name']}")

    # share of debt from stored ciphertext under a naive ordering
    def share_archives(order, s="base"):
        f = schedule(order)
        tot = sum(debt_at(j, f[j], s) for j in range(N))
        arc = sum(debt_at(j, f[j], s) for j in range(N) if items[j]["kind"] == "archive")
        return arc / tot
    print(f"\nArchive share of debt (Mosca order, base): {share_archives(strategies['Mosca X+Y ranking'])*100:.1f}%")
    print(f"Archive share of debt (Q-RIN order, base): {share_archives(strategies['Q-RIN debt-optimal'])*100:.1f}%")

    json.dump({k: v for k, v in res.items()}, open("results.json", "w"), indent=1)
