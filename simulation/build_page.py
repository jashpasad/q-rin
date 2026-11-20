"""Embed simulation outputs into page_template.html and write ../index.html.
Run after harvest_debt_sim.py, robustness.py, export_demo_data.py and export_more.py."""
import json

d = json.load(open("demo_data.json"))
e = json.load(open("more_data.json"))
for s in d["strategies"].values():
    for o in s["order"]:
        o["start"] = round(o["start"], 1)
        o["finish"] = round(o["finish"], 1)
    for sc in d["scenarios"]:
        s[sc]["curve"] = [round(x) for x in s[sc]["curve"]]
        s[sc]["total"] = round(s[sc]["total"])
e["cdf"] = {k: [round(x, 4) for x in v] for k, v in e["cdf"].items()}
for r in e["ledger"]:
    r["rate"] = round(r["rate"], 1)
    r["ratio"] = round(r["ratio"], 1)
    r["finish"] = round(r["finish"], 1)

t = open("page_template.html").read()
t = t.replace("__DATA__", json.dumps(d, separators=(",", ":")))
t = t.replace("__MORE__", json.dumps(e, separators=(",", ":")))
open("../index.html", "w").write(t)
print("wrote ../index.html")
