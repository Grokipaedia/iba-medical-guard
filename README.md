# iba-medical-guard

> **Medical AI that never acts without verified human intent.**

---

## The Stakes

AI is entering clinical workflows. Diagnostics. Treatment recommendations. Dosage adjustments. Patient monitoring. Digital health twins. Prescription management.

Every one of those is a life-critical authorization event.

Who signed the intent before the AI touched the patient record?
Which clinician? Under what scope? With what limits?
What happens if the AI drifts beyond the declared procedure?
What is the kill threshold before the AI takes an action no clinician authorized?

**These are not theoretical questions. They are the questions every hospital, insurer, and regulator will ask — before and after an incident.**

---

## The Gap

Current medical AI deployments — clinical decision support, diagnostic AI, patient monitoring agents — operate with:

- Implicit access to patient records
- No declared clinician intent certificate
- No cryptographic boundary on what actions are permitted
- No kill threshold for high-risk recommendations
- No immutable audit chain traceable to a specific licensed clinician

An AI that recommends a dosage adjustment without a signed intent from the prescribing clinician is operating outside its authorization — regardless of how confident the model is.

**The model's confidence is not authorization. The clinician's signed intent is.**

---

## The IBA Layer

```
┌─────────────────────────────────────────────────────┐
│           LICENSED CLINICIAN · HUMAN PRINCIPAL      │
│   Signs .iba.yaml before any clinical AI action     │
│   Declares patient consent, procedure scope,        │
│   data access limits, and kill threshold            │
└───────────────────────┬─────────────────────────────┘
                        │  Signed Intent Certificate
                        │  · Clinician ID + license
                        │  · Patient consent reference
                        │  · Declared procedure scope
                        │  · Forbidden: prescription, surgery, discharge
                        │  · Kill threshold
                        │  · Hard session expiry
                        ▼
┌─────────────────────────────────────────────────────┐
│              IBA MEDICAL GUARD                      │
│   Validates certificate before every               │
│   clinical AI action, data access, or              │
│   treatment recommendation                          │
│                                                     │
│   No cert = No clinical AI action                  │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│         MEDICAL AI SYSTEM                           │
│   Clinical decision support · Diagnostic AI         │
│   Patient monitoring · Digital health twins         │
│   Any medical AI agent or clinical workflow tool    │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
git clone https://github.com/Grokipaedia/iba-medical-guard.git
cd iba-medical-guard
pip install -r requirements.txt
python guard.py "review patient labs and recommend dosage adjustment" --hollow medium
```

---

## Configuration — .iba.yaml

```yaml
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
  - lab_review
  - lab_read
  - medication_review
  - dosage_recommend
  - monitoring_read
  - notes_read
  - vitals_read

denied:
  - new_prescription
  - surgery
  - discharge
  - procedure_order
  - external_data_share
  - insurance_report
  - data_export

default_posture: DENY_ALL

kill_threshold: "surgery | invasive_procedure | emergency_protocol_override | unauthorized_prescription | data_breach"

temporal_scope:
  hard_expiry: "2026-04-17T23:59:59"
  session_max_hours: 4

audit:
  chain: witnessbound
  log_every_action: true
  clinician_signature_required: true
```

---

## Gate Logic

```
Valid clinician certificate?               → PROCEED
Patient consent reference present?        → PROCEED
Action outside declared scope?            → BLOCK
Forbidden action attempted?               → BLOCK
Kill threshold triggered?                 → TERMINATE + LOG
Session expired?                          → BLOCK
No certificate present?                   → BLOCK
```

**No cert = No clinical AI action. No model accesses patient data without a signed clinician intent.**

---

## The Clinical Authorization Events

| Action | Without IBA | With IBA |
|--------|-------------|---------|
| Read patient lab results | Implicit — any record | Explicit — declared patient only |
| Review medication history | Implicit | Declared scope only |
| Recommend dosage adjustment | Implicit — any medication | Declared medication scope only |
| Write new prescription | No boundary exists | FORBIDDEN — BLOCK |
| Order invasive procedure | No boundary exists | KILL THRESHOLD — TERMINATE |
| Override emergency protocol | No boundary exists | KILL THRESHOLD — TERMINATE |
| Share data externally | No boundary exists | FORBIDDEN — BLOCK |
| Access without consent | No boundary exists | FORBIDDEN — BLOCK |
| Export patient records | No boundary exists | FORBIDDEN — BLOCK |

---

## Why This Matters for Regulators

The EU AI Act classifies medical AI as **high-risk**. High-risk AI systems must have:

- Human oversight mechanisms
- Logging and traceability of decisions
- Clear accountability for every AI-generated output

The FDA's AI/ML-Based Software as a Medical Device (SaMD) framework requires:

- Predetermined change control plans
- Real-world performance monitoring
- Transparency in AI decision-making

HIPAA requires:

- Minimum necessary access to patient data
- Audit trails for all access to protected health information
- Authorization controls traceable to a responsible party

**IBA provides the cryptographic primitive that makes all of these requirements enforceable at the execution layer — not the policy layer.**

---

## Safe Hollowing — Patient Data Protection

```bash
# Light — redact direct identifiers only
python guard.py "review patient record" --hollow light

# Medium — redact identifiers + diagnosis + medication
python guard.py "review patient record" --hollow medium

# Deep — redact all PHI before AI sees the data
python guard.py "review patient record" --hollow deep
```

The AI sees only what the cert permits it to see.

---

## Live Demo

**governinglayer.com/governor-html/**

Edit the cert. Run any clinical AI action. Watch the gate fire — ALLOW · BLOCK · TERMINATE. Sub-1ms gate latency confirmed.

---

## Patent & Standards Record

```
Patent:   GB2603013.0 (Pending) · UK IPO · Filed February 10, 2026
WIPO DAS: Confirmed April 15, 2026 · Access Code C9A6
PCT:      150+ countries · Protected until August 2028
IETF:     draft-williams-intent-token-00 · CONFIRMED LIVE
          datatracker.ietf.org/doc/draft-williams-intent-token/
NIST:     13 filings · NIST-2025-0035
NCCoE:    10 filings · AI Agent Identity & Authorization
```

IBA priority date: **February 10, 2026**
EU AI Act high-risk classification: **August 2026**
FDA SaMD framework: Active
HIPAA: Active

IBA provides prior art coverage for medical AI authorization across all three regulatory frameworks.

---

## Related Repos

| Repo | Gap closed |
|------|-----------|
| [iba-governor](https://github.com/Grokipaedia/iba-governor) | Full production governance · working implementation |
| [iba-twin-guard](https://github.com/Grokipaedia/iba-twin-guard) | Digital twin identity · health twin governance |
| [iba-platform-guard](https://github.com/Grokipaedia/iba-platform-guard) | Every managed agent platform |
| [iba-mythos-governor](https://github.com/Grokipaedia/iba-mythos-governor) | Mythos-ready security program |

---

## Acquisition Enquiries

IBA Intent Bound Authorization is available for acquisition.

**Jeffrey Williams**
IBA@intentbound.com
IntentBound.com
Patent GB2603013.0 Pending · WIPO DAS C9A6 · IETF draft-williams-intent-token-00
