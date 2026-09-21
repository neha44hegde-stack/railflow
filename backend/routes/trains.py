from flask import Blueprint, request, jsonify
from extensions import db
from models import Train, TrainStation, Station, TrainClass
from utils.decorators import admin_required
from utils.audit import log_action

trains_bp = Blueprint("trains", __name__, url_prefix="/api/trains")

TRAIN_TYPES = {"Express", "Superfast", "Intercity", "Passenger", "Other"}


@trains_bp.route("", methods=["GET"])
def list_trains():
    trains = Train.query.order_by(Train.train_number).all()
    return jsonify({"trains": [t.to_dict() for t in trains]})


@trains_bp.route("/<int:tid>", methods=["GET"])
def get_train(tid):
    t = Train.query.get(tid)
    if not t:
        return jsonify({"error": "Train not found"}), 404
    return jsonify({"train": t.to_dict()})


@trains_bp.route("", methods=["POST"])
@admin_required
def create_train():
    data = request.get_json() or {}
    number = (data.get("train_number") or "").strip()
    name = (data.get("train_name") or "").strip()
    ttype = data.get("train_type")
    if not number or not name or not ttype:
        return jsonify({"error": "train_number, train_name, train_type required"}), 400
    if ttype not in TRAIN_TYPES:
        return jsonify({"error": "Invalid train_type"}), 400
    if Train.query.filter_by(train_number=number).first():
        return jsonify({"error": "Train number already exists"}), 409
    t = Train(train_number=number, train_name=name, train_type=ttype, status="ACTIVE")
    db.session.add(t)
    db.session.flush()
    log_action("create", "train", t.id, f"Added {t.train_number} - {t.train_name}")
    db.session.commit()
    return jsonify({"train": t.to_dict()}), 201


@trains_bp.route("/<int:tid>", methods=["PUT"])
@admin_required
def update_train(tid):
    t = Train.query.get(tid)
    if not t:
        return jsonify({"error": "Train not found"}), 404
    data = request.get_json() or {}
    if "train_number" in data:
        num = data["train_number"].strip()
        existing = Train.query.filter_by(train_number=num).first()
        if existing and existing.id != tid:
            return jsonify({"error": "Train number already exists"}), 409
        t.train_number = num
    if "train_name" in data:
        t.train_name = data["train_name"].strip()
    if "train_type" in data:
        if data["train_type"] not in TRAIN_TYPES:
            return jsonify({"error": "Invalid train_type"}), 400
        t.train_type = data["train_type"]
    log_action("update", "train", t.id, f"Updated {t.train_number}")
    db.session.commit()
    return jsonify({"train": t.to_dict()})


@trains_bp.route("/<int:tid>/status", methods=["PATCH"])
@admin_required
def set_status(tid):
    t = Train.query.get(tid)
    if not t:
        return jsonify({"error": "Train not found"}), 404
    data = request.get_json() or {}
    status = data.get("status")
    if status not in ("ACTIVE", "INACTIVE"):
        return jsonify({"error": "Invalid status"}), 400
    t.status = status
    log_action("status_change", "train", t.id, f"{t.train_number} -> {status}")
    db.session.commit()
    return jsonify({"train": t.to_dict()})


@trains_bp.route("/<int:tid>/route", methods=["GET"])
def get_route(tid):
    if not Train.query.get(tid):
        return jsonify({"error": "Train not found"}), 404
    stops = (TrainStation.query.filter_by(train_id=tid)
             .order_by(TrainStation.stop_number).all())
    return jsonify({"route": [s.to_dict() for s in stops]})


@trains_bp.route("/<int:tid>/route", methods=["POST"])
@admin_required
def add_route_stop(tid):
    if not Train.query.get(tid):
        return jsonify({"error": "Train not found"}), 404
    data = request.get_json() or {}
    station_id = data.get("station_id")
    stop_number = data.get("stop_number")
    if not station_id or stop_number is None:
        return jsonify({"error": "station_id and stop_number required"}), 400
    if not Station.query.get(station_id):
        return jsonify({"error": "Station not found"}), 404
    if TrainStation.query.filter_by(train_id=tid, station_id=station_id).first():
        return jsonify({"error": "Station already on this route"}), 409
    if TrainStation.query.filter_by(train_id=tid, stop_number=stop_number).first():
        return jsonify({"error": "Stop number already used"}), 409
    ts = TrainStation(train_id=tid, station_id=station_id, stop_number=int(stop_number),
                     arrival_time=data.get("arrival_time"),
                     departure_time=data.get("departure_time"),
                     distance_km=float(data.get("distance_km") or 0))
    db.session.add(ts)
    db.session.flush()
    log_action("route_add", "train", tid, f"Added stop {stop_number}")
    db.session.commit()
    return jsonify({"stop": ts.to_dict()}), 201


@trains_bp.route("/<int:tid>/route/<int:rid>", methods=["PUT"])
@admin_required
def update_route_stop(tid, rid):
    ts = TrainStation.query.filter_by(id=rid, train_id=tid).first()
    if not ts:
        return jsonify({"error": "Stop not found"}), 404
    data = request.get_json() or {}
    if "stop_number" in data:    ts.stop_number = int(data["stop_number"])
    if "arrival_time" in data:   ts.arrival_time = data["arrival_time"]
    if "departure_time" in data: ts.departure_time = data["departure_time"]
    if "distance_km" in data:    ts.distance_km = float(data["distance_km"] or 0)
    log_action("route_update", "train", tid, f"Updated stop {rid}")
    db.session.commit()
    return jsonify({"stop": ts.to_dict()})


@trains_bp.route("/<int:tid>/route/<int:rid>", methods=["DELETE"])
@admin_required
def delete_route_stop(tid, rid):
    ts = TrainStation.query.filter_by(id=rid, train_id=tid).first()
    if not ts:
        return jsonify({"error": "Stop not found"}), 404
    db.session.delete(ts)
    log_action("route_delete", "train", tid, f"Removed stop {rid}")
    db.session.commit()
    return jsonify({"message": "Deleted"})


@trains_bp.route("/<int:tid>/classes", methods=["GET"])
def get_classes(tid):
    classes = TrainClass.query.filter_by(train_id=tid).all()
    src = request.args.get("source")
    dst = request.args.get("destination")
    if src and dst:
        try:
            src_ts = TrainStation.query.filter_by(train_id=tid, station_id=int(src)).first()
            dst_ts = TrainStation.query.filter_by(train_id=tid, station_id=int(dst)).first()
            if src_ts and dst_ts:
                dist = max(float(dst_ts.distance_km or 0) - float(src_ts.distance_km or 0), 0)
                if dist > 0:
                    result = []
                    for c in classes:
                        d = c.to_dict()
                        d["fare"] = round(float(c.fare) * (dist / 100.0), 2)
                        d["distance_km"] = dist
                        result.append(d)
                    return jsonify({"classes": result})
        except Exception:
            pass
    return jsonify({"classes": [c.to_dict() for c in classes]})


@trains_bp.route("/<int:tid>/classes", methods=["POST"])
@admin_required
def add_class(tid):
    if not Train.query.get(tid):
        return jsonify({"error": "Train not found"}), 404
    data = request.get_json() or {}
    cname = data.get("class_name")
    total = data.get("total_seats")
    fare = data.get("fare")
    prefix = data.get("seat_prefix") or "S"
    if not cname or total is None or fare is None:
        return jsonify({"error": "class_name, total_seats, fare required"}), 400
    try:
        total = int(total); fare = float(fare)
    except Exception:
        return jsonify({"error": "Invalid numeric values"}), 400
    if total <= 0 or fare < 0:
        return jsonify({"error": "total_seats must be > 0 and fare >= 0"}), 400
    if TrainClass.query.filter_by(train_id=tid, class_name=cname).first():
        return jsonify({"error": "Class already exists for this train"}), 409
    tc = TrainClass(train_id=tid, class_name=cname, total_seats=total,
                    fare=fare, seat_prefix=prefix)
    db.session.add(tc)
    db.session.flush()
    log_action("class_add", "train", tid, f"Added class {cname} ({total} seats, Rs.{fare})")
    db.session.commit()
    return jsonify({"class": tc.to_dict()}), 201


@trains_bp.route("/<int:tid>/classes/<int:cid>", methods=["PUT"])
@admin_required
def update_class(tid, cid):
    tc = TrainClass.query.filter_by(id=cid, train_id=tid).first()
    if not tc:
        return jsonify({"error": "Class not found"}), 404
    data = request.get_json() or {}
    if "total_seats" in data:
        try:
            v = int(data["total_seats"])
            if v <= 0: return jsonify({"error": "total_seats must be > 0"}), 400
            tc.total_seats = v
        except Exception:
            return jsonify({"error": "Invalid total_seats"}), 400
    if "fare" in data:
        try:
            v = float(data["fare"])
            if v < 0: return jsonify({"error": "fare must be >= 0"}), 400
            tc.fare = v
        except Exception:
            return jsonify({"error": "Invalid fare"}), 400
    log_action("class_update", "train", tid, f"Updated class {cid}")
    db.session.commit()
    return jsonify({"class": tc.to_dict()})


@trains_bp.route("/<int:tid>/classes/<int:cid>", methods=["DELETE"])
@admin_required
def delete_class(tid, cid):
    tc = TrainClass.query.filter_by(id=cid, train_id=tid).first()
    if not tc:
        return jsonify({"error": "Class not found"}), 404
    db.session.delete(tc)
    log_action("class_delete", "train", tid, f"Deleted class {cid}")
    db.session.commit()
    return jsonify({"message": "Deleted"})