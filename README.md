# iba-medical-guard

**Medical AI that never acts without verified human intent.**

As AI enters clinical workflows — diagnostics, treatment recommendations, patient monitoring, digital health twins — the risk of unauthorized or drifted actions is no longer theoretical.

`iba-medical-guard` adds real cryptographic governance to any medical AI agent.

Every action (data access, recommendation, prescription, monitoring command) must respect a signed **IBA Intent Certificate** from a licensed clinician.

## Features
- Requires IBA-signed intent before any medical action
- Enforces strict scope (patient consent, clinician authority, approved procedures)
- Prevents unauthorized data access or treatment changes
- Optional safe hollowing / redaction of sensitive patient data
- Works with any medical AI system or clinical decision support tool

## Patent & Filings
- **Patent Pending**: GB2603013.0 (filed 5 Feb 2026, PCT route open — 150+ countries)
- **NIST Docket**: NIST-2025-0035 (13 IBA filings)
- **NCCoE Filings**: 10 submissions on AI agent authorization

## Quick Start
```bash
git clone https://github.com/Grokipaedia/iba-medical-guard.git
cd iba-medical-guard
pip install -r requirements.txt
python guard.py "review patient labs and recommend dosage adjustment" --hollow medium
