from flask_jwt_extended import get_jwt_identity
from extensions import db
from models import AuditLog


def log_action(action, entity, entity_id=None, details=""):
    try:
        uid = int(get_jwt_identity())
    except Exception:
        uid = None
    db.session.add(AuditLog(
        user_id=uid, action=action, entity=entity,
        entity_id=entity_id, details=details,
    ))
