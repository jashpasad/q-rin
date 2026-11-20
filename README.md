# Q-RIN: Harvest-Debt Engine for Quantum-Ready Finance

**Team Jalebi** — Jash Pasad, Beli Dedhia (IIT Gandhinagar)
Submission to the GIFT FutureLab Grand Challenge 2026–27.

Adversaries can record encrypted traffic and steal encrypted archives today, then decrypt them once a cryptographically relevant quantum computer exists ("harvest now, decrypt later"). Every month a bank keeps RSA or elliptic-curve cryptography on a channel, it adds to that pile.

Q-RIN (ऋण, *debt*) treats this as an accruing liability, **harvest debt**. It:

1. **Discovers** quantum-vulnerable key exchange and key wrapping without decrypting anything (TLS/IPsec/SSH handshakes, PGP/CMS headers, X.509, HSM/KMS inventories).
2. **Prices** each flow or archive: volume × value × harvest probability × P(quantum computer arrives before the secret expires).
3. **Plans** the debt-optimal migration order: a weighted-completion-time scheduling problem with dependencies, parallel teams and uncertain quantum-arrival time (minimax regret).
4. **Devalues** data that may already be stolen: hybrid ML-KEM tunnels, archive re-wrapping, secret rotation.
5. **Supervises**: sector-level debt metric for regulators.

**Interactive results page:** open `index.html`, or the GitHub Pages site if enabled.

## Preliminary results (synthetic)

| Finding | Value |
|---|---|
| Median harvest-debt reduction vs best standard heuristic, 120 randomised banks | **47%** (IQR 43–51%, worst 23%) |
| Base bank vs Mosca X+Y ranking, same effort and finish date | 50% less |
| Q-RIN with 3 teams vs Mosca ranking with 6 teams | 1.77M vs 1.93M units |
| Cost of starting the optimal plan 12 months late | +119% |
| Share of debt in the top 5 of 32 systems | 82% |
| Regret vs per-scenario optimum | 1–5% |

All bank parameters are synthetic and stylised from public specifications. Debt is in relative value units. The results show the size of the ordering effect, not a forecast for any real institution.

## Model

```
D_j = ∫₀^{C_j} r_j · F(t + L_j) dt        total debt = Σ_j D_j

r_j  harvestable value per month (flows: records/month × value × P(recorded);
     archives: stored records × value × P(stolen per month))
L_j  secrecy lifetime of the data class
F    CDF of quantum-computer arrival time (three lognormal scenarios)
C_j  completion month of system j's migration
```

## Reproduce

```bash
cd simulation
pip install numpy scipy
python harvest_debt_sim.py     # base bank, all strategies
python robustness.py           # 120 randomised banks
python export_demo_data.py     # data for the page
python export_more.py          # extra analyses
python build_page.py           # rebuilds ../index.html
```

## Key references

- Gidney (2025), *How to factor 2048 bit RSA integers with less than a million noisy qubits*, arXiv:2505.15917
- Babbush et al. (2026), *Securing elliptic curve cryptocurrencies against quantum vulnerabilities*, PRX Quantum 7, 031001
- Mosca & Piani (2025), *Quantum Threat Timeline Report 2025*, Global Risk Institute
- Auer et al. (2025), *Quantum-readiness for the financial system: a roadmap*, BIS Papers No 158
- G7 Cyber Expert Group (2026), PQC roadmap for the financial sector
- NIST IR 8547 (2026, final), *Transition to post-quantum cryptography standards*
- DST, Government of India (2026), *Report on Quantum-Safe Ecosystem in India*
- RBI (2026), Q-SAFE expert committee; IFSCA (2026), cyber security guidelines for MIIs
- Smith (1956), *Various optimizers for single-stage production*

Full list on the results page.
