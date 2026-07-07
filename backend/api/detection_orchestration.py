"""
Unified Detection Pipeline API Routes

Orchestrates the complete pipeline:

 1. Network capture (realtime)
 2. Packet processing & feature extraction
 3. Autoencoder anomaly detection
 4. LightGBM attack classification
 5. SHAP explainability
 6. Severity assessment
 7. Analyst approval & decision-making  ← HITL (DB-backed, server-enforced timeout)
 8. Response actions (block, isolate, quarantine)
 9. Drift detection & RL model updates
10. Forensic report generation with LLM
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
from datetime import datetime
import json

# Import orchestration components
try:
    from realtime.inference.inference_engine import InferenceEngine
    from realtime.response.response_manager import ResponseEngine
    from realtime.response.hitl_manager import HITLManager
    from realtime.drift.adwin_engine import ADWINEngine
    from realtime.rl.policy_engine import PolicyEngine
    from backend.llm.report_generator import generate_llm_report
except ImportError as e:
    print(f"Warning: Could not import detection components: {e}")

from backend.core.database import get_db, SessionLocal
from backend.models.alert import Alert
from backend.models.detection import Detection
from backend.models.incident import Incident

router = APIRouter(tags=["Detection Pipeline"])

# ---------------------------------------------------------------------------
# Singleton engines — lazy init
# ---------------------------------------------------------------------------
_inference_engine = None
_response_engine  = None
_hitl_manager     = None
_adwin_engine     = None
_rl_engine        = None


def _get_engines():
    """Lazy initialisation — shared singletons within this process."""
    global _inference_engine, _response_engine, _hitl_manager, _adwin_engine, _rl_engine

    if _inference_engine is None:
        _inference_engine = InferenceEngine()
        _response_engine  = ResponseEngine()
        _hitl_manager     = HITLManager()       # DB-backed — process-safe
        _adwin_engine     = ADWINEngine()
        _rl_engine        = PolicyEngine()

    return _inference_engine, _response_engine, _hitl_manager, _adwin_engine, _rl_engine


# ---------------------------------------------------------------------------
# STARTUP: enforce timeouts for any approvals still pending in the DB
# ---------------------------------------------------------------------------

def _enforce_hitl_timeouts():
    """
    Called on a background schedule every 10 seconds.
    Closes any pending approvals whose deadline has passed and
    optionally triggers the response engine.
    """
    try:
        hitl = HITLManager()
        expired_ids = hitl.get_expired_pending()
        for detection_id in expired_ids:
            result = hitl.handle_timeout(detection_id)
            if result.get("auto_executed"):
                try:
                    _, re, *_ = _get_engines()
                    re.execute(result["detection"], approved=True)
                except Exception as exc:
                    print(f"[HITL-Timeout] Auto-response failed for {detection_id}: {exc}")
            print(f"[HITL-Timeout] Enforced timeout for {detection_id}")
    except Exception as exc:
        print(f"[HITL-Timeout] Scheduler error: {exc}")


# ---------------------------------------------------------------------------
# PROCESS DETECTION
# ---------------------------------------------------------------------------

@router.post("/detection/process")
async def process_detection(
    features: Dict,
    background_tasks: BackgroundTasks,
    db=None,
):
    """
    Process a feature dict through the complete pipeline.

    Args:
        features: dict with AT MINIMUM the 6 ML features plus network metadata
                  (source_ip, destination_ip, source_port, destination_port, protocol,
                   duration, packet_count, mean_packet_size, std_packet_size,
                   total_bytes, mean_iat)

    Returns:
        Detection result with all pipeline stage outputs.
    """
    try:
        ie, re, hitl, adwin, rl = _get_engines()

        # ── STEP 3: AUTOENCODER ANOMALY DETECTION ──────────────────────────
        # Build the correctly scaled feature DataFrame before calling the model
        ml_features = {
            k: features[k]
            for k in ["duration", "packet_count", "mean_packet_size",
                      "std_packet_size", "total_bytes", "mean_iat"]
            if k in features
        }
        df_scaled = ie.scale_features(ie.prepare_features(ml_features))
        ae_score  = ie.anomaly_score(df_scaled)
        is_anomaly = ae_score > ie.threshold

        result = {
            "pipeline_id":     f"DETECT-{datetime.utcnow().timestamp():.0f}",
            "timestamp":       datetime.utcnow().isoformat(),
            "source_ip":       features.get("source_ip", ""),
            "destination_ip":  features.get("destination_ip", ""),
            "source_port":     features.get("source_port"),
            "destination_port": features.get("destination_port"),
            "protocol":        str(features.get("protocol", "")),
            "anomaly_detected": is_anomaly,
            "steps":           {},
        }

        result["steps"]["autoencoder"] = {
            "status":       "complete",
            "is_anomaly":   is_anomaly,
            "anomaly_score": ae_score,
        }

        if not is_anomaly:
            result["classification"] = {"attack_type": "BENIGN", "confidence": 1.0}
            result["severity"] = "LOW"
            result["status"]   = "benign"
            return result

        # ── STEP 4: LIGHTGBM CLASSIFICATION ────────────────────────────────
        classification = ie.classifier.classify(ml_features)
        result["steps"]["classification"] = {
            "status":            "complete",
            "classification_id": classification["classification"],
            "confidence":        classification["confidence"],
        }

        # ── STEP 5: SHAP EXPLAINABILITY ─────────────────────────────────────
        shap_explanation = ie.shap_engine.explain(ml_features)   # 6 features only
        result["steps"]["shap_explainability"] = {
            "status":            "complete",
            "feature_importance": shap_explanation,
            "explanation":        str(shap_explanation),
        }

        # ── STEP 6: SEVERITY ASSESSMENT ─────────────────────────────────────
        risk_input = {
            "is_anomaly":    True,
            "classification": classification["classification"],
            "confidence":    classification["confidence"],
            "anomaly_score": ae_score,
        }
        risk = ie.risk_engine.evaluate(risk_input)
        severity    = risk.get("severity",   "MEDIUM")
        risk_score  = risk.get("risk_score", 50)
        attack_type = risk.get("attack_type", "Unknown")

        result.update({
            "severity":         severity,
            "risk_score":       risk_score,
            "attack_type":      attack_type,
            "anomaly_score":    ae_score,
            "confidence":       classification["confidence"],
            "shap_explanation": shap_explanation,
        })
        result["steps"]["severity_assessment"] = {
            "status":     "complete",
            "severity":   severity,
            "risk_score": risk_score,
            "attack_type": attack_type,
        }

        # Build suggested actions for the HITL dialog
        suggested_actions = re.get_suggested_actions(severity, attack_type)
        result["response_actions"] = suggested_actions

        # ── STEP 7: HITL ────────────────────────────────────────────────────
        hitl_input = {
            "id":              result["pipeline_id"],
            "pipeline_id":     result["pipeline_id"],
            "severity":        severity,
            "attack_type":     attack_type,
            "source_ip":       result["source_ip"],
            "destination_ip":  result["destination_ip"],
            "source_port":     result["source_port"],
            "destination_port": result["destination_port"],
            "protocol":        result["protocol"],
            "anomaly_score":   ae_score,
            "risk_score":      risk_score,
            "confidence":      classification["confidence"],
            "explanations":    shap_explanation,
            "response_actions": suggested_actions,
        }
        hitl_decision = hitl.process(hitl_input)

        result["steps"]["analyst_approval"] = {
            "status":           "pending" if hitl_decision["requires_analyst"] else "complete",
            "requires_analyst": hitl_decision["requires_analyst"],
            "action":           hitl_decision["action"],
            "timeout_seconds":  hitl_decision["timeout_seconds"],
            "created_at":       hitl_decision["created_at"],
        }
        result["analyst_approval"] = hitl_decision

        if not hitl_decision["requires_analyst"]:
            # ── STEP 8 (AUTO): RESPONSE ──────────────────────────────────────
            response_result = re.execute(result, approved=True)
            result["steps"]["response"] = {
                "status":          "complete",
                "actions_executed": response_result["actions_executed"],
                "action_level":    response_result.get("action_level", "none"),
            }
            result["response"] = response_result
        else:
            result["response"] = {
                "status":           "pending_approval",
                "suggested_actions": suggested_actions,
            }
            # Trigger the UI HITL Pop-up — INLINE, not background
            print(f"[HITL-PUSH] Severity={severity}, requires_analyst=True, pushing WebSocket notification NOW...")
            try:
                from backend.api.websocket_routes import push_hitl, _connections
                ws_payload = {
                    "detection_id": hitl_decision.get("detection_id"),
                    "timeout_seconds": hitl_decision.get("timeout_seconds"),
                    "action": hitl_decision.get("action"),
                    "detection": {
                        "attack_type": result.get("attack_type"),
                        "source_ip": result.get("source_ip"),
                        "confidence": result.get("confidence"),
                        "shap_explanation": result.get("shap_explanation")
                    }
                }
                hitl_subscribers = len(_connections.get("hitl", set()))
                print(f"[HITL-PUSH] Active HITL WebSocket subscribers: {hitl_subscribers}")
                print(f"[HITL-PUSH] Payload: {ws_payload}")
                await push_hitl(ws_payload)
                print(f"[HITL-PUSH] Successfully broadcast to {hitl_subscribers} subscriber(s)")
            except Exception as push_exc:
                print(f"[HITL-PUSH] FAILED: {push_exc}")
                import traceback
                traceback.print_exc()

        # ── STEP 9: DRIFT DETECTION ─────────────────────────────────────────
        drift_status = adwin.update(risk_score / 100.0)
        result["steps"]["drift_detection"] = {
            "status":        "complete",
            "drift_detected": drift_status["drift_detected"],
            "estimation":    drift_status["estimation"],
        }
        # ── STEP 10: RL POLICY UPDATE ───────────────────────────────────────
        # Always learn from anomaly detections to build the Q-table
        background_tasks.add_task(_update_rl_model, result["pipeline_id"], result)
        result["rl_update"] = {"status": "scheduled", "reason": "anomaly_detected"}

        if drift_status["drift_detected"]:
            background_tasks.add_task(_update_rl_from_drift, result, drift_status["estimation"])
            result["rl_update"]["drift_learning"] = True

        result["status"] = "anomaly_detected"

        # ── Write to Alert + possibly Incident ──────────────────────────────
        background_tasks.add_task(_persist_detection_as_alert, result)
        background_tasks.add_task(_async_push_alert_notification, result)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# ANALYST DECISIONS
# ---------------------------------------------------------------------------

@router.post("/detection/{detection_id}/approve")
async def approve_detection(
    detection_id: str,
    notes: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
):
    """Analyst approves detection — triggers response execution and RL learning."""
    try:
        _, re, hitl, _, rl = _get_engines()
        decision = hitl.analyst_decision(detection_id, "approve", notes)
        if decision.get("status") == "error":
            raise HTTPException(status_code=404, detail=decision["message"])

        response_result = re.execute(decision["detection"], approved=True)

        # RL learns from analyst approval (positive reinforcement)
        rl.learn_from_analyst_decision(decision["detection"], "approve")

        return {
            "status":           "approved",
            "detection_id":     detection_id,
            "analyst_notes":    notes,
            "response_executed": response_result,
            "rl_update":        "learning_from_approval",
            "timestamp":        datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detection/{detection_id}/reject")
async def reject_detection(detection_id: str, notes: Optional[str] = None):
    """Analyst rejects detection (false alarm) — triggers RL learning."""
    try:
        _, _, hitl, _, rl = _get_engines()
        decision = hitl.analyst_decision(detection_id, "reject", notes)
        if decision.get("status") == "error":
            raise HTTPException(status_code=404, detail=decision["message"])

        rl.learn_from_false_alarm(decision["detection"])
        return {
            "status":       "rejected",
            "detection_id": detection_id,
            "analyst_notes": notes,
            "reason":       "false_alarm",
            "rl_update":    "learning_from_false_alarm",
            "timestamp":    datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detection/{detection_id}/investigate")
async def investigate_detection(detection_id: str, notes: Optional[str] = None):
    """Analyst flags detection for further investigation."""
    try:
        _, _, hitl, *_ = _get_engines()
        decision = hitl.analyst_decision(detection_id, "investigate", notes)
        if decision.get("status") == "error":
            raise HTTPException(status_code=404, detail=decision["message"])
        return {
            "status":       "investigating",
            "detection_id": detection_id,
            "analyst_notes": notes,
            "timestamp":    datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detection/{detection_id}/timeout")
async def timeout_detection(detection_id: str):
    """
    Called by the UI when its local countdown reaches zero.
    Confirms the backend timeout and triggers auto-response if configured.
    This is a belt-and-suspenders complement to the server-side scheduler.
    """
    try:
        _, re, hitl, *_ = _get_engines()
        result = hitl.handle_timeout(detection_id)
        if result.get("status") == "error":
            # Already resolved (by scheduler or another client) — not an error
            return {"status": "already_resolved", "detection_id": detection_id}

        if result.get("auto_executed"):
            re.execute(result["detection"], approved=True)

        return {
            "status":       "timeout",
            "detection_id": detection_id,
            "auto_executed": result.get("auto_executed", False),
            "timestamp":    datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# QUERIES
# ---------------------------------------------------------------------------

@router.get("/detection/pending-approvals")
async def get_pending_approvals():
    """Get all detections pending analyst approval (DB-backed)."""
    try:
        _, _, hitl, *_ = _get_engines()
        pending = hitl.get_pending_approvals()
        return {
            "count":            len(pending),
            "pending_approvals": pending,
            "timestamp":        datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detection/response-history")
async def get_response_history(limit: int = 100):
    """Get response action execution history."""
    try:
        _, re, *_ = _get_engines()
        history = re.get_response_history(limit)
        return {"total": len(history), "history": history, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detection/drift-status")
def get_drift_status():
    """Get current ADWIN drift detection status."""
    try:
        _, _, _, adwin, _ = _get_engines()
        status = adwin.get_status()
        return {
            "drift_detected": status.get("drift_detected", False),
            "estimation":     status.get("estimation", 0.0),
            "timestamp":      datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detection/{detection_id}/report")
async def generate_detection_report(detection_id: str, report_format: str = "json"):
    """Generate LLM forensic report (text).  File formats handled by /api/reports/."""
    try:
        llm_report = generate_llm_report({"detection_id": detection_id, "timestamp": datetime.utcnow().isoformat()})
        return {
            "detection_id":  detection_id,
            "report_format": report_format,
            "llm_analysis":  llm_report,
            "generated_at":  datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# BACKGROUND TASKS
# ---------------------------------------------------------------------------

def _update_rl_model(detection_id: str, detection_data: Dict):
    try:
        _, _, _, _, rl = _get_engines()
        rl.learn_from_detection(detection_data)
        print(f"[RL] Model updated for {detection_id}")
    except Exception as e:
        print(f"[RL] Error updating model: {e}")


def _update_rl_from_drift(detection_data: Dict, drift_value: float):
    try:
        _, _, _, _, rl = _get_engines()
        rl.learn_from_drift(detection_data, drift_value)
        print(f"[RL] Drift learning applied (drift={drift_value:.4f})")
    except Exception as e:
        print(f"[RL] Error in drift learning: {e}")


def _persist_detection_as_alert(result: Dict):
    """
    Write anomalous detections to the Alert table so the UI can see them.
    Also auto-creates an Incident for HIGH/CRITICAL severity.
    Pushes a WebSocket notification to all connected alert subscribers.
    """
    import uuid as _uuid
    import json as _json
    import asyncio as _asyncio

    if not result.get("anomaly_detected"):
        return

    db = SessionLocal()
    try:
        alert = Alert(
            id                      = result.get("pipeline_id", str(_uuid.uuid4())),
            source_ip               = result.get("source_ip", "0.0.0.0"),
            destination_ip          = result.get("destination_ip", "0.0.0.0"),
            source_port             = result.get("source_port"),
            destination_port        = result.get("destination_port"),
            protocol                = str(result.get("protocol", "")),
            attack_type             = result.get("attack_type", "UNKNOWN"),
            severity                = result.get("severity", "MEDIUM"),
            risk_score              = float(result.get("risk_score", 50)),
            confidence              = float(result.get("confidence", 0)) * 100,
            anomaly_score           = result.get("anomaly_score"),
            classification_confidence = result.get("confidence"),
            shap_explanation        = _json.dumps(result.get("shap_explanation")) if result.get("shap_explanation") else None,
        )
        db.add(alert)

        # Auto-create Incident for HIGH/CRITICAL
        if result.get("severity") in ("HIGH", "CRITICAL"):
            incident = Incident(
                id          = str(_uuid.uuid4()),
                start_time  = datetime.utcnow(),
                attack_type = result.get("attack_type", "UNKNOWN"),
                source_ip   = result.get("source_ip", "0.0.0.0"),
                severity    = result.get("severity", "HIGH"),
                alert_count = 1,
            )
            db.add(incident)

        db.commit()
    except Exception as exc:
        print(f"[Persist] Failed to write alert/incident: {exc}")
        db.rollback()
    finally:
        db.close()

async def _async_push_alert_notification(result: dict):
    """Pushes an alert to the WebSocket asynchronously."""
    try:
        from backend.api.websocket_routes import push_alert
        ws_payload = {
            "id":           result.get("pipeline_id"),
            "attack_type":  result.get("attack_type"),
            "severity":     result.get("severity"),
            "risk_score":   result.get("risk_score"),
            "source_ip":    result.get("source_ip"),
            "destination_ip": result.get("destination_ip"),
        }
        await push_alert(ws_payload)
    except Exception as ws_exc:
        print(f"[Persist] WebSocket push failed: {ws_exc}")


async def _async_push_hitl_notification(hitl_decision: dict, result: dict):
    """Pushes a HITL approval request to the WebSocket asynchronously."""
    try:
        from backend.api.websocket_routes import push_hitl
        ws_payload = {
            "detection_id": hitl_decision.get("detection_id"),
            "timeout_seconds": hitl_decision.get("timeout_seconds"),
            "action": hitl_decision.get("action"),
            "detection": {
                "attack_type": result.get("attack_type"),
                "source_ip": result.get("source_ip"),
                "confidence": result.get("confidence"),
                "shap_explanation": result.get("shap_explanation")
            }
        }
        await push_hitl(ws_payload)
    except Exception as ws_exc:
        print(f"[Persist] WebSocket HITL push failed: {ws_exc}")
