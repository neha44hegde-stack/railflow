from flask import Blueprint, request, jsonify
from extensions import db
from models import Station
from utils.decorators import admin_required
from utils.audit import log_action

stations_bp = Blueprint("stations", __name__, url_prefix="/api/stations")


@stations_bp.route("", methods=["GET"])
def list_stations():
    q = (request.args.get("q") or "").strip()
    query = Station.query
    if q:
        like = f"%{q}%"
        query = query.filter((Station.name.ilike(like)) | (Station.code.ilike(like)) | (Station.city.ilike(like)))
    return jsonify({"stations": [s.to_dict() for s in query.order_by(Station.name).all()]})


@stations_bp.route("", methods=["POST"])
@admin_required
def create_station():
    data = request.get_json() or {}
    for f in ("name", "code", "city", "state"):
        if not str(data.get(f) or "").strip():
            return jsonify({"error": f"{f} is required"}), 400
    code = data["code"].strip().upper()
    if Station.query.filter_by(code=code).first():
        return jsonify({"error": "Station code already exists"}), 409
    s = Station(name=data["name"].strip(), code=code,
                city=data["city"].strip(), state=data["state"].strip())
    db.session.add(s)
    db.session.flush()
    log_action("create", "station", s.id, f"Added {s.code} - {s.name}")
    db.session.commit()
    return jsonify({"station": s.to_dict()}), 201


@stations_bp.route("/<int:sid>", methods=["PUT"])
@admin_required
def update_station(sid):
    s = Station.query.get(sid)
    if not s:
        return jsonify({"error": "Station not found"}), 404
    data = request.get_json() or {}
    if "code" in data:
        code = data["code"].strip().upper()
        existing = Station.query.filter_by(code=code).first()
        if existing and existing.id != sid:
            return jsonify({"error": "Station code already exists"}), 409
        s.code = code
    if "name" in data:  s.name = data["name"].strip()
    if "city" in data:  s.city = data["city"].strip()
    if "state" in data: s.state = data["state"].strip()
    log_action("update", "station", s.id, f"Updated {s.code}")
    db.session.commit()
    return jsonify({"station": s.to_dict()})


@stations_bp.route("/<int:sid>", methods=["DELETE"])
@admin_required
def delete_station(sid):
    s = Station.query.get(sid)
    if not s:
        return jsonify({"error": "Station not found"}), 404
    code = s.code
    log_action("delete", "station", sid, f"Deleted {code}")
    db.session.delete(s)
    db.session.commit()
    return jsonify({"message": "Deleted"})
