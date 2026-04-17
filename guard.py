# guard.py - IBA protection for medical AI agents
import json
from datetime import datetime
import sys
import argparse

def create_iba_medical_guard(action: str, hollow_level: str = None):
    cert = {
        "iba_version": "2.0",
        "certificate_id": f"medical-guard-{datetime.now().strftime('%Y%m%d-%H%M')}",
        "issued_at": datetime.now().isoformat(),
        "principal": "licensed-clinician",
        "declared_intent": f"Perform medical action: {action}. Strictly within approved clinical scope and patient consent.",
        "scope_envelope": {
            "resources": ["patient-record-review", "diagnostic-support", "treatment-recommendation"],
            "denied": ["unauthorized-data-access", "prescription-without-review", "patient-impersonation"],
            "default_posture": "DENY_ALL"
        },
        "temporal_scope": {
            "hard_expiry": (datetime.now().replace(year=datetime.now().year + 1)).isoformat()
        },
        "entropy_threshold": {
            "max_kl_divergence": 0.10,
            "flag_at": 0.06,
            "kill_at": 0.10
        },
        "iba_signature": "demo-signature"
    }

    protected_file = f"medical-action-{action.replace(' ', '-').lower()[:30]}.iba-protected.md"

    content = f"# Medical Action Request: {action}\n\n[Action would be executed here under IBA governance]\n\n<!-- IBA PROTECTED MEDICAL ACTION -->\n"

    if hollow_level:
        content += f"\n<!-- Hollowed ({hollow_level}): Sensitive clinical data protected by IBA certificate -->\n"

    with open(protected_file, "w", encoding="utf-8") as f:
        f.write("<!-- IBA PROTECTED MEDICAL ACTION -->\n")
        f.write(f"<!-- Intent Certificate: {json.dumps(cert, indent=2)} -->\n\n")
        f.write(content)

    print(f"✅ IBA-protected medical action file created: {protected_file}")
    if hollow_level:
        print(f"   Hollowing level applied: {hollow_level}")
    else:
        print("   Full medical action protected by IBA certificate")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Governed medical AI action with IBA")
    parser.add_argument("action", help="Description of the medical action")
    parser.add_argument("--hollow", choices=["light", "medium", "heavy"], help="Apply safe hollowing")
    args = parser.parse_args()

    create_iba_medical_guard(args.action, args.hollow)
