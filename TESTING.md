# Testing iba-medical-guard

No terminal required. Test in your browser in 3 minutes using Google Colab.

---

## Browser Test — Google Colab

**Step 1** — Open [colab.research.google.com](https://colab.research.google.com) · New notebook

**Step 2** — Run Cell 1:
```python
!pip install pyyaml
```

**Step 3** — Run Cell 2 — create the clinical intent certificate:
```python
iba_yaml = """
intent:
  description: "Review lab results for Patient A-4471 and recommend dosage adjustment for existing medication only. No new prescriptions. No surgery. No discharge."

clinician:
  id: "DR-WILLIAMS-NPI-1234567890"
  license: "MD-LICENSE-GB-2024-XXXX"
  specialty: "internal_medicine"

patient:
  consent_reference: "CONSENT-A4471-2026-04-17"
  data_access: "read_only"

scope:
  - lab
  - read
  - review
  - vitals
  - medication
  - monitoring
  - notes
  - recommend
  - dosage

denied:
  - new_prescription
  - prescription
  - surgery
  - discharge
  - export
  - insurance
  - external
  - order additional
  - procedure

default_posture: DENY_ALL

kill_threshold: "surgery | invasive_procedure | emergency_protocol_override | override emergency"

temporal_scope:
  hard_expiry: "2026-12-31"
"""

with open(".iba.yaml", "w") as f:
    f.write(iba_yaml)

print("Clinical intent certificate written.")
```

**Step 4** — Run Cell 3 — run the medical guard:
```python
import json, yaml, os, time
from datetime import datetime, timezone

class IBABlockedError(Exception): pass
class IBATerminatedError(Exception): pass

class IBAMedicalGuard:
    def __init__(self):
        self.terminated = False
        self.action_count = 0
        self.block_count = 0
        self.recommendations = []
        self.session_id = f"clinical-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        with open(".iba.yaml") as f:
            cfg = yaml.safe_load(f)
        self.scope = [s.lower() for s in cfg.get("scope", [])]
        self.denied = [d.lower() for d in cfg.get("denied", [])]
        self.kill_threshold = [t.strip().lower() for t in str(cfg.get("kill_threshold","")).split("|")]
        self.default_posture = cfg.get("default_posture", "DENY_ALL")
        self.clinician = cfg.get("clinician", {})
        self.patient = cfg.get("patient", {})
        print(f"✅ IBA Medical Guard loaded · Session: {self.session_id}")
        print(f"   Clinician : {self.clinician.get('id','UNKNOWN')} · {self.clinician.get('specialty','')}")
        print(f"   Consent   : {self.patient.get('consent_reference','NONE')}")
        print(f"   Scope     : {', '.join(self.scope)}")
        print(f"   Denied    : {', '.join(self.denied)}\n")

    def check_action(self, action):
        if self.terminated:
            raise IBATerminatedError("Clinical session terminated.")
        self.action_count += 1
        a = action.lower()

        if any(k in a for k in self.kill_threshold if k):
            self.terminated = True
            print(f"  ✗ TERMINATE [{action}]\n    → Kill threshold — clinical session ended")
            raise IBATerminatedError(f"Kill threshold: {action}")

        if any(d in a for d in self.denied if d):
            self.block_count += 1
            print(f"  ✗ BLOCKED   [{action}]\n    → Action in denied list")
            raise IBABlockedError(f"Denied: {action}")

        if self.scope and not any(s in a for s in self.scope):
            if self.default_posture == "DENY_ALL":
                self.block_count += 1
                print(f"  ✗ BLOCKED   [{action}]\n    → Outside declared clinical scope (DENY_ALL)")
                raise IBABlockedError(f"Out of scope: {action}")

        print(f"  ✓ ALLOWED   [{action}]")
        return True

    def log_recommendation(self, rec, confidence):
        self.recommendations.append(rec)
        print(f"  ◎ RECOMMEND [{rec}] (confidence: {confidence:.0%})")
        print(f"    → Logged · Requires clinician approval before implementation")

guard = IBAMedicalGuard()

scenarios = [
    ("Read patient lab results — Patient A-4471",           "Haemoglobin 11.2 g/dL, consider iron supplementation", 0.87),
    ("Review current medication list — Patient A-4471",     None, None),
    ("Read patient vitals — last 24h monitoring",           None, None),
    ("Read clinical notes — attending physician",           None, None),
    ("Write new prescription — amoxicillin 500mg",         None, None),
    ("Export patient records to external insurance portal", None, None),
    ("Order additional lab tests — full blood panel",       None, None),
    ("Override emergency protocol — patient A-4471",       None, None),
]

for action, recommendation, confidence in scenarios:
    try:
        guard.check_action(action)
        if recommendation:
            guard.log_recommendation(recommendation, confidence)
    except IBATerminatedError:
        break
    except IBABlockedError:
        pass

print(f"\n{'═'*60}")
print(f"  Actions: {guard.action_count} · Blocked: {guard.block_count} · Recommendations: {len(guard.recommendations)}")
print(f"  Clinician: {guard.clinician.get('id','UNKNOWN')}")
print(f"  Status : {'TERMINATED' if guard.terminated else 'COMPLETE'}")
print(f"{'═'*60}")
```

---

## Expected Output

```
✅ IBA Medical Guard loaded · Session: clinical-...
   Clinician : DR-WILLIAMS-NPI-1234567890 · internal_medicine
   Consent   : CONSENT-A4471-2026-04-17

  ✓ ALLOWED   [Read patient lab results — Patient A-4471]
  ◎ RECOMMEND [Haemoglobin 11.2 g/dL, consider iron supplementation] (confidence: 87%)
    → Logged · Requires clinician approval before implementation
  ✓ ALLOWED   [Review current medication list — Patient A-4471]
  ✓ ALLOWED   [Read patient vitals — last 24h monitoring]
  ✓ ALLOWED   [Read clinical notes — attending physician]
  ✗ BLOCKED   [Write new prescription — amoxicillin 500mg]
    → Action in denied list
  ✗ BLOCKED   [Export patient records to external insurance portal]
    → Action in denied list
  ✗ BLOCKED   [Order additional lab tests — full blood panel]
    → Action in denied list
  ✗ TERMINATE [Override emergency protocol — patient A-4471]
    → Kill threshold — clinical session ended

════════════════════════════════════════════════════════════
  Actions: 8 · Blocked: 3 · Recommendations: 1
  Clinician: DR-WILLIAMS-NPI-1234567890
  Status : TERMINATED
════════════════════════════════════════════════════════════
```

---

## With PHI Hollowing

```bash
# Redact patient identifiers before AI processes data
python guard.py "review patient record for john smith dob 1965-03-12" --hollow medium
```

---

## Local Test

```bash
git clone https://github.com/Grokipaedia/iba-medical-guard.git
cd iba-medical-guard
pip install -r requirements.txt
python guard.py --demo
```

---

## Live Demo

**governinglayer.com/governor-html/**

Edit the cert. Run any clinical AI action. See the gate fire.

---

IBA Intent Bound Authorization · Patent GB2603013.0 Pending · WIPO DAS C9A6
IBA@intentbound.com · IntentBound.com
