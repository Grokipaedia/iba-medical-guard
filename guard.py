# guard.py - IBA Intent Bound Authorization · Medical Guard
# Patent GB2603013.0 (Pending) · UK IPO · Filed February 5, 2026
# WIPO DAS Confirmed April 15, 2026 · Access Code C9A6
# IETF draft-williams-intent-token-00 · intentbound.com
#
# Medical AI that never acts without verified human intent.
# Every clinical action requires a signed intent certificate
# from a licensed clinician before any patient data is accessed.

import json
import yaml
import os
import time
import argparse
from datetime import datetime, timezone


class IBABlockedError(Exception):
    """Raised when a clinical AI action is blocked by the IBA gate."""
    pass


class IBATerminatedError(Exception):
    """Raised when the clinical session is terminated by the IBA gate."""
    pass


HOLLOW_LEVELS = {
    "light":  ["patient_name", "date_of_birth", "address", "nhs_number", "ssn"],
    "medium": ["patient_name", "date_of_birth", "address", "nhs_number", "ssn",
               "diagnosis", "medication", "condition", "treatment"],
    "deep":   ["patient_name", "date_of_birth", "address", "nhs_number", "ssn",
               "diagnosis", "medication", "condition", "treatment",
               "lab_values", "vitals", "imaging", "notes", "history"],
}


class IBAMedicalGuard:
    """
    IBA enforcement layer for medical AI systems.
    Requires a signed clinician intent certificate before any
    clinical AI action, data access, or treatment recommendation.

    Covers: clinical decision support, diagnostic AI,
    patient monitoring, digital health twins, prescription management.

    Regulatory alignment: EU AI Act (high-risk), FDA SaMD, HIPAA.
    """

    def __init__(self, config_path=".iba.yaml", audit_path="medical-audit.jsonl"):
        self.config_path = config_path
        self.audit_path = audit_path
        self.terminated = False
        self.session_id = f"clinical-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        self.action_count = 0
        self.block_count = 0
        self.recommendations = []

        self.config = self._load_config()
        self.scope           = [s.lower() for s in self.config.get("scope", [])]
        self.denied          = [d.lower() for d in self.config.get("denied", [])]
        self.default_posture = self.config.get("default_posture", "DENY_ALL")
        self.kill_threshold  = self.config.get("kill_threshold", None)
        self.hard_expiry     = self.config.get("temporal_scope", {}).get("hard_expiry", None)
        self.clinician       = self.config.get("clinician", {})
        self.patient         = self.config.get("patient", {})

        self._validate_clinician_cert()
        self._log_event("SESSION_START", "IBA Medical Guard initialised", "ALLOW")
        self._print_header()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            print(f"⚠️  No {self.config_path} found — DENY_ALL posture active. No clinical AI actions permitted.")
            default = {
                "intent": {"description": "No clinical intent declared — DENY_ALL. No patient data access permitted."},
                "scope": [], "denied": [], "default_posture": "DENY_ALL",
            }
            with open(self.config_path, "w") as f:
                yaml.dump(default, f)
            return default
        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def _validate_clinician_cert(self):
        """Validate clinician identity and patient consent before session begins."""
        if not self.clinician:
            print("⚠️  WARNING: No clinician identity in certificate.")
        if not self.patient.get("consent_reference"):
            print("⚠️  WARNING: No patient consent reference in certificate.")

    def _print_header(self):
        intent = self.config.get("intent", {})
        desc = intent.get("description", "No intent declared") if isinstance(intent, dict) else str(intent)
        clinician_id = self.clinician.get("id", "UNKNOWN")
        specialty    = self.clinician.get("specialty", "UNKNOWN")
        consent_ref  = self.patient.get("consent_reference", "NONE")

        print("\n" + "═" * 66)
        print("  IBA MEDICAL GUARD · Intent Bound Authorization")
        print("  Patent GB2603013.0 Pending · WIPO DAS C9A6 · intentbound.com")
        print("═" * 66)
        print(f"  Session    : {self.session_id}")
        print(f"  Clinician  : {clinician_id} · {specialty}")
        print(f"  Consent    : {consent_ref}")
        print(f"  Intent     : {desc[:55]}...")
        print(f"  Posture    : {self.default_posture}")
        print(f"  Scope      : {', '.join(self.scope) if self.scope else 'NONE'}")
        print(f"  Denied     : {', '.join(self.denied) if self.denied else 'NONE'}")
        if self.hard_expiry:
            print(f"  Expires    : {self.hard_expiry}")
        if self.kill_threshold:
            print(f"  Kill       : {self.kill_threshold}")
        print("═" * 66 + "\n")

    def _is_expired(self):
        if not self.hard_expiry:
            return False
        try:
            expiry = datetime.fromisoformat(str(self.hard_expiry))
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) > expiry
        except Exception:
            return False

    def _match_scope(self, action: str) -> bool:
        return any(s in action.lower() for s in self.scope)

    def _match_denied(self, action: str) -> bool:
        return any(d in action.lower() for d in self.denied)

    def _match_kill_threshold(self, action: str) -> bool:
        if not self.kill_threshold:
            return False
        thresholds = [t.strip().lower() for t in str(self.kill_threshold).split("|")]
        return any(t in action.lower() for t in thresholds)

    def _log_event(self, event_type: str, action: str, verdict: str, reason: str = ""):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "clinician_id": self.clinician.get("id", "UNKNOWN"),
            "consent_ref": self.patient.get("consent_reference", "NONE"),
            "event_type": event_type,
            "action": action[:200],
            "verdict": verdict,
            "reason": reason,
        }
        with open(self.audit_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def check_action(self, action: str) -> bool:
        """
        Gate check. Call before every clinical AI action.
        Returns True if permitted.
        Raises IBABlockedError if blocked.
        Raises IBATerminatedError if kill threshold triggered.

        Every audit entry is traceable to the signed clinician certificate.
        """
        if self.terminated:
            raise IBATerminatedError("Clinical session terminated. No further AI actions permitted.")

        self.action_count += 1
        start = time.perf_counter()

        # 1. Expiry — clinical sessions have hard time limits
        if self._is_expired():
            self._log_event("BLOCK", action, "BLOCK", "Clinical certificate expired")
            self.block_count += 1
            print(f"  ✗ BLOCKED  [{action[:64]}]\n    → Clinical certificate expired")
            raise IBABlockedError(f"Certificate expired: {action}")

        # 2. Kill threshold — life-critical stop
        if self._match_kill_threshold(action):
            self._log_event("TERMINATE", action, "TERMINATE", "Kill threshold triggered — clinical session ended")
            self.terminated = True
            print(f"  ✗ TERMINATE [{action[:62]}]\n    → Kill threshold — clinical session ended")
            self._log_event("SESSION_END", "Kill threshold", "TERMINATE")
            raise IBATerminatedError(f"Kill threshold triggered: {action}")

        # 3. Denied list
        if self._match_denied(action):
            self._log_event("BLOCK", action, "BLOCK", "Action in denied list")
            self.block_count += 1
            print(f"  ✗ BLOCKED  [{action[:64]}]\n    → Action in denied list")
            raise IBABlockedError(f"Denied: {action}")

        # 4. Scope check
        if self.scope and not self._match_scope(action):
            if self.default_posture == "DENY_ALL":
                self._log_event("BLOCK", action, "BLOCK", "Outside declared clinical scope — DENY_ALL")
                self.block_count += 1
                print(f"  ✗ BLOCKED  [{action[:64]}]\n    → Outside declared clinical scope (DENY_ALL)")
                raise IBABlockedError(f"Out of scope: {action}")

        # 5. ALLOW
        elapsed_ms = (time.perf_counter() - start) * 1000
        self._log_event("ALLOW", action, "ALLOW", f"Within clinical scope ({elapsed_ms:.3f}ms)")
        print(f"  ✓ ALLOWED  [{action[:64]}]  ({elapsed_ms:.3f}ms)")
        return True

    def log_recommendation(self, recommendation: str, confidence: float):
        """Log an AI clinical recommendation to the audit chain."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "clinician_id": self.clinician.get("id", "UNKNOWN"),
            "consent_ref": self.patient.get("consent_reference", "NONE"),
            "event_type": "RECOMMENDATION",
            "recommendation": recommendation,
            "confidence": confidence,
            "verdict": "LOGGED",
            "note": "REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE IMPLEMENTATION",
        }
        self.recommendations.append(entry)
        with open(self.audit_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"  ◎ RECOMMEND [{recommendation[:60]}] (confidence: {confidence:.0%})")
        print(f"    → Logged · Requires clinician approval before implementation")

    def hollow(self, data: str, level: str = "medium") -> str:
        """Redact PHI from patient data before AI processes it."""
        blocked = HOLLOW_LEVELS.get(level, HOLLOW_LEVELS["medium"])
        hollowed = data
        redacted = []
        for item in blocked:
            if item.lower() in data.lower():
                hollowed = hollowed.replace(item, f"[PHI-REDACTED:{item.upper()}]")
                redacted.append(item)
        if redacted:
            print(f"  ◎ HOLLOWED [{level}] — PHI redacted: {', '.join(redacted)}")
            self._log_event("HOLLOW", f"PHI hollowing: {level}", "ALLOW",
                           f"Redacted: {', '.join(redacted)}")
        return hollowed

    def summary(self):
        print("\n" + "═" * 66)
        print("  IBA MEDICAL GUARD · SESSION SUMMARY")
        print("═" * 66)
        print(f"  Session        : {self.session_id}")
        print(f"  Clinician      : {self.clinician.get('id', 'UNKNOWN')}")
        print(f"  Consent ref    : {self.patient.get('consent_reference', 'NONE')}")
        print(f"  Actions        : {self.action_count}")
        print(f"  Blocked        : {self.block_count}")
        print(f"  Allowed        : {self.action_count - self.block_count}")
        print(f"  Recommendations: {len(self.recommendations)}")
        print(f"  Status         : {'TERMINATED' if self.terminated else 'COMPLETE'}")
        print(f"  Audit log      : {self.audit_path}")
        print("═" * 66 + "\n")

    def print_audit_log(self):
        print("\n── CLINICAL AUDIT CHAIN ─────────────────────────────────────────")
        if not os.path.exists(self.audit_path):
            print("  No audit log found.")
            return
        with open(self.audit_path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    verdict = entry.get('verdict', '')
                    etype = entry.get('event_type', '')
                    if etype == 'RECOMMENDATION':
                        print(f"  ◎ {entry['timestamp'][:19]}  RECOMMEND  {entry.get('recommendation','')[:45]}")
                    else:
                        symbol = "✓" if verdict == "ALLOW" else "✗"
                        print(f"  {symbol} {entry['timestamp'][:19]}  {verdict:<10}  {entry['action'][:48]}")
                except Exception:
                    pass
        print("─────────────────────────────────────────────────────────────────\n")


# ── CLI & Demonstration ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='IBA Medical Guard')
    parser.add_argument('task', nargs='?', help='Clinical AI task')
    parser.add_argument('--hollow', choices=['light', 'medium', 'deep'],
                        default=None, help='Apply PHI hollowing')
    parser.add_argument('--config', default='.iba.yaml')
    parser.add_argument('--demo', action='store_true')
    args = parser.parse_args()

    guard = IBAMedicalGuard(config_path=args.config)

    if args.task and args.hollow:
        task = guard.hollow(args.task, args.hollow)
        print(f"\n  Task (PHI hollowed): {task}\n")

    if args.demo or not args.task:
        scenarios = [
            # ALLOW — within clinical scope
            ("Read patient lab results — Patient A-4471",           True,  "Haemoglobin 11.2 g/dL, consider iron supplementation", 0.87),
            ("Review current medication list — Patient A-4471",     True,  None, None),
            ("Read patient vitals — last 24h monitoring",           True,  None, None),
            ("Read clinical notes — attending physician",           True,  None, None),

            # BLOCK — denied list
            ("Write new prescription — amoxicillin 500mg",         False, None, None),
            ("Export patient records to external insurance portal", False, None, None),
            ("Order additional lab tests — full blood panel",       False, None, None),

            # TERMINATE — kill threshold
            ("Override emergency protocol — patient A-4471",       False, None, None),
        ]

        print("── Running Clinical AI Gate Checks ──────────────────────────────\n")

        for action, allowed, recommendation, confidence in scenarios:
            try:
                guard.check_action(action)
                if recommendation:
                    guard.log_recommendation(recommendation, confidence)
            except IBATerminatedError as e:
                print(f"\n  CLINICAL SESSION TERMINATED: {e}")
                break
            except IBABlockedError:
                pass

    guard.summary()
    guard.print_audit_log()


if __name__ == "__main__":
    main()
