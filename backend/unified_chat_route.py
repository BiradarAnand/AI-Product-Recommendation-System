from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from occasion_nlp import OCCASION_LABELS, OCCASION_ICONS
from occasion_engine import OCCASION_CATEGORIES
from agents.coordinator_agent import CoordinatorAgent

unified_chat_bp = Blueprint("unified_chat", __name__)
coordinator = CoordinatorAgent()

@unified_chat_bp.route("/api/chat/unified", methods=["POST"])
def unified_chat():
    data        = request.get_json() or {}
    message     = (data.get("message") or "").strip()
    history     = data.get("history")     or []
    refinements = data.get("refinements") or {}

    if not message:
        return jsonify({"error": "message is required"}), 400

    # Resolve user_id (JWT optional — guest fallback)
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception:
        pass
    if not user_id:
        user_id = data.get("user_id")

    context = {
        "user_id": user_id,
        "history": history,
        "refinements": refinements
    }

    try:
        result = coordinator.process(message, context)
        return jsonify(result)
    except Exception as e:
        print(f"[unified_chat] error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@unified_chat_bp.route("/api/chat/occasions", methods=["GET"])
def list_occasions():
    return jsonify([
        {"key": k, "label": OCCASION_LABELS[k], "icon": OCCASION_ICONS[k]}
        for k in OCCASION_CATEGORIES
    ])