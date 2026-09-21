from datetime import datetime
from flask import Blueprint, request, jsonify
from models import Train, TrainStation, TrainClass
from services.seat_service import available_seats

search_bp = Blueprint("search", __name__, url_prefix="/api/trains")


@search_bp.route("/search", methods=["GET"])
def search_trains():
    src_id = request.args.get("source")
    dst_id = request.args.get("destination")
    date_str = request.args.get("date")
    cls = request.args.get("class")
    ttype = request.args.get("train_type")

    if not src_id or not dst_id:
        return jsonify({"error": "source and destination are required"}), 400

    try:
        src_id = int(src_id); dst_id = int(dst_id)
    except Exception:
        return jsonify({"error": "Invalid station ids"}), 400

    if src_id == dst_id:
        return jsonify({"trains": [], "count": 0})

    jd = None
    if date_str:
        try:
            jd = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return jsonify({"error": "Invalid date format"}), 400

    src_stops = {ts.train_id: ts for ts in TrainStation.query.filter_by(station_id=src_id).all()}
    dst_stops = {ts.train_id: ts for ts in TrainStation.query.filter_by(station_id=dst_id).all()}
    common = set(src_stops) & set(dst_stops)

    results = []
    for tid in common:
        src = src_stops[tid]; dst = dst_stops[tid]
        if src.stop_number >= dst.stop_number:
            continue
        train = Train.query.get(tid)
        if not train or train.status != "ACTIVE":
            continue
        if ttype and train.train_type != ttype:
            continue
        classes = TrainClass.query.filter_by(train_id=tid).all()
        if cls:
            classes = [c for c in classes if c.class_name == cls]
        if not classes:
            continue

        # distance and per-passenger fare
        try:
            s_km = float(src.distance_km or 0)
            d_km = float(dst.distance_km or 0)
            distance = max(d_km - s_km, 0)
        except Exception:
            distance = 0

        class_info = []
        for c in classes:
            if jd:
                total, booked, avail = available_seats(tid, jd, c.class_name)
            else:
                total, booked, avail = c.total_seats, 0, c.total_seats
            if distance > 0:
                fare = round(float(c.fare) * (distance / 100.0), 2)
            else:
                fare = float(c.fare)
            class_info.append({
                "class_name": c.class_name, "fare": fare,
                "total_seats": total, "available_seats": avail,
            })

        results.append({
            "train": train.to_dict(), "source": src.to_dict(), "destination": dst.to_dict(),
            "departure": src.departure_time, "arrival": dst.arrival_time,
            "distance_km": distance,
            "classes": class_info,
        })

    results.sort(key=lambda x: x["train"]["train_number"])
    return jsonify({"trains": results, "count": len(results)})
