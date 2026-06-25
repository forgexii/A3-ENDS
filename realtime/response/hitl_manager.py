"""
Human-In-The-Loop Manager  (DB-backed)

Routes detections based on severity and analyst policies.
Persists all pending approvals to SQLite so that:
  - State is shared between the realtime runner and FastAPI endpoints
  - Timeouts are enforced by a backend scheduler (not a UI-side timer)
  - Process restarts do not lose pending approvals
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from backend.core.database import SessionLocal
from backend.models.hitl_approval import HITLApproval

logger = logging.getLogger(__name__)


# In-memory fallback when the DB table is not yet available
# (e.g. first run before create_all, or read-only DB during development)
_MEMORY_STORE: Dict[str, dict] = {}
_USE_MEMORY_FALLBACK = False

# Timeout rules per severity (seconds)
TIMEOUT_MAP = {
    "LOW":      0,    # no analyst review
    "MEDIUM":   300,  # 5 minutes
    "HIGH":     300,  # 5 minutes (auto-execute after)
    "CRITICAL": 60,   # 1 minute  (auto-execute after)
}

AUTO_EXECUTE_SEVERITIES = {"HIGH", "CRITICAL"}


class HITLManager:
    """Manage analyst approval workflows — all state lives in SQLite."""

    # ------------------------------------------------------------------
    # ROUTING
    # ------------------------------------------------------------------

    def process(self, detection: Dict) -> Dict:
        """
        Route detection based on severity.

        Writes a HITLApproval row to the DB if analyst review is required.

        Args:
            detection: Detection dict (must contain 'severity', 'id' or
                       'pipeline_id', plus network/ML fields).

        Returns:
            Decision dict with action, requires_analyst, timeout_seconds,
            created_at (ISO string) so the UI can compute remaining time.
        """
        severity = detection.get("severity", "LOW")
        detection_id = detection.get("id") or detection.get("pipeline_id") or str(uuid.uuid4())
        timeout_seconds = TIMEOUT_MAP.get(severity, 300)
        auto_execute   = severity in AUTO_EXECUTE_SEVERITIES

        decision = {
            "detection_id":     detection_id,
            "severity":         severity,
            "requires_analyst": False,
            "action":           "LOG_ONLY",
            "auto_response":    False,
            "timeout_seconds":  0,
            "created_at":       datetime.utcnow().isoformat(),
            "timestamp":        datetime.utcnow().isoformat(),
        }

        if severity == "LOW":
            decision["action"] = "LOG_ONLY"
            logger.info("[HITL] Low severity — logging only")
            return decision

        # Medium / High / Critical → analyst review required
        decision["requires_analyst"] = True
        decision["timeout_seconds"]  = timeout_seconds
        decision["auto_response"]    = auto_execute
        decision["action"] = {
            "MEDIUM":   "ANALYST_REVIEW",
            "HIGH":     "ESCALATE",
            "CRITICAL": "IMMEDIATE_RESPONSE",
        }.get(severity, "ANALYST_REVIEW")

        # Persist to DB
        self._create_approval(detection_id, detection, severity, timeout_seconds, auto_execute)

        logger.warning(
            f"[HITL] {severity} detection {detection_id} — analyst review required "
            f"(timeout={timeout_seconds}s, auto_execute={auto_execute})"
        )
        return decision

    # ------------------------------------------------------------------
    # ANALYST DECISION
    # ------------------------------------------------------------------

    def analyst_decision(
        self,
        detection_id: str,
        decision: str,           # "approve" | "reject" | "investigate"
        notes: Optional[str] = None,
    ) -> Dict:
        """Record analyst decision and close the approval."""
        db = SessionLocal()
        try:
            row = db.query(HITLApproval).filter(
                HITLApproval.id == detection_id,
                HITLApproval.status == "pending",
            ).first()

            if not row:
                return {"status": "error", "message": f"No pending approval for {detection_id}"}

            status_map = {
                "approve":     "approved",
                "reject":      "rejected",
                "investigate": "investigated",
            }
            row.status       = status_map.get(decision, decision)
            row.analyst_notes = notes
            row.resolved_at  = datetime.utcnow()
            db.commit()

            detection = self._row_to_detection(row)
            result = {
                "detection_id":    detection_id,
                "analyst_decision": decision,
                "notes":           notes,
                "action":          {"approve": "execute", "reject": "skip", "investigate": "investigate"}.get(decision, "skip"),
                "approved":        decision == "approve",
                "rejected":        decision == "reject",
                "detection":       detection,
                "timestamp":       datetime.utcnow().isoformat(),
            }
            logger.info(f"[HITL] Analyst {decision.upper()} {detection_id}")
            return result
        finally:
            db.close()

    # ------------------------------------------------------------------
    # TIMEOUT ENFORCEMENT (called by scheduler)
    # ------------------------------------------------------------------

    def handle_timeout(self, detection_id: str) -> Dict:
        """
        Called by the backend scheduler when a pending approval expires.
        Marks the row as 'timeout' and returns auto-execute flag.
        """
        db = SessionLocal()
        try:
            row = db.query(HITLApproval).filter(
                HITLApproval.id == detection_id,
                HITLApproval.status == "pending",
            ).first()

            if not row:
                return {"status": "error", "message": f"No pending approval for {detection_id}"}

            row.status      = "timeout"
            row.resolved_at = datetime.utcnow()
            db.commit()

            detection  = self._row_to_detection(row)
            auto_exec  = row.auto_execute
            result = {
                "detection_id": detection_id,
                "timeout":      True,
                "auto_executed": auto_exec,
                "action":       "execute_automatically" if auto_exec else "skip",
                "detection":    detection,
                "timestamp":    datetime.utcnow().isoformat(),
            }
            logger.warning(f"[HITL] TIMEOUT for {detection_id} — auto_execute={auto_exec}")
            return result
        finally:
            db.close()

    # ------------------------------------------------------------------
    # QUERIES
    # ------------------------------------------------------------------

    def get_pending_approvals(self) -> Dict:
        """Return all pending approvals as a dict keyed by detection_id."""
        db = SessionLocal()
        try:
            rows = db.query(HITLApproval).filter(
                HITLApproval.status == "pending"
            ).all()
            result = {}
            for row in rows:
                result[row.id] = {
                    "detection":    self._row_to_detection(row),
                    "created_at":   row.created_at.isoformat(),
                    "timeout_seconds": row.timeout_seconds,
                    "auto_execute": row.auto_execute,
                    "severity":     row.severity,
                }
            return result
        finally:
            db.close()

    def get_expired_pending(self) -> List[str]:
        """Return IDs of pending approvals whose timeout has elapsed."""
        from datetime import timedelta
        db = SessionLocal()
        try:
            rows = db.query(HITLApproval).filter(
                HITLApproval.status == "pending"
            ).all()
            now = datetime.utcnow()
            expired = []
            for row in rows:
                deadline = row.created_at + timedelta(seconds=row.timeout_seconds)
                if now >= deadline:
                    expired.append(row.id)
            return expired
        finally:
            db.close()

    def get_approval_history(self, limit: int = 100) -> List[Dict]:
        """Return resolved approvals (newest first)."""
        db = SessionLocal()
        try:
            rows = db.query(HITLApproval).filter(
                HITLApproval.status != "pending"
            ).order_by(HITLApproval.resolved_at.desc()).limit(limit).all()
            return [self._row_to_dict(row) for row in rows]
        finally:
            db.close()

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _create_approval(
        self,
        detection_id: str,
        detection: Dict,
        severity: str,
        timeout_seconds: int,
        auto_execute: bool,
    ):
        """Write a new HITLApproval row, ignoring duplicates."""
        db = SessionLocal()
        try:
            existing = db.query(HITLApproval).filter(HITLApproval.id == detection_id).first()
            if existing:
                return  # Already registered

            shap_raw = detection.get("explanations") or detection.get("shap_explanation")
            actions  = detection.get("response_actions") or detection.get("suggested_actions")

            row = HITLApproval(
                id              = detection_id,
                severity        = severity,
                timeout_seconds = timeout_seconds,
                auto_execute    = auto_execute,
                attack_type     = detection.get("attack_type"),
                source_ip       = detection.get("source_ip"),
                dest_ip         = detection.get("destination_ip") or detection.get("dest_ip"),
                source_port     = detection.get("source_port"),
                dest_port       = detection.get("destination_port") or detection.get("dest_port"),
                protocol        = str(detection.get("protocol", "")),
                anomaly_score   = detection.get("anomaly_score"),
                risk_score      = detection.get("risk_score"),
                confidence      = detection.get("confidence"),
                shap_explanation= json.dumps(shap_raw) if shap_raw else None,
                response_actions= json.dumps(actions)  if actions  else None,
                status          = "pending",
                created_at      = datetime.utcnow(),
            )
            db.add(row)
            db.commit()
        except Exception as exc:
            logger.error(f"[HITL] Failed to persist approval {detection_id}: {exc}")
            db.rollback()
        finally:
            db.close()

    def _row_to_detection(self, row: HITLApproval) -> Dict:
        shap = None
        if row.shap_explanation:
            try:
                shap = json.loads(row.shap_explanation)
            except Exception:
                pass
        actions = None
        if row.response_actions:
            try:
                actions = json.loads(row.response_actions)
            except Exception:
                pass
        return {
            "id":           row.id,
            "severity":     row.severity,
            "attack_type":  row.attack_type,
            "source_ip":    row.source_ip,
            "dest_ip":      row.dest_ip,
            "source_port":  row.source_port,
            "destination_port": row.dest_port,
            "protocol":     row.protocol,
            "anomaly_score": row.anomaly_score,
            "risk_score":   row.risk_score,
            "confidence":   row.confidence,
            "shap_explanation": shap,
            "response_actions": actions or [],
            "created_at":   row.created_at.isoformat(),
            "timeout_seconds": row.timeout_seconds,
        }

    def _row_to_dict(self, row: HITLApproval) -> Dict:
        d = self._row_to_detection(row)
        d.update({
            "status":      row.status,
            "analyst_notes": row.analyst_notes,
            "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None,
        })
        return d