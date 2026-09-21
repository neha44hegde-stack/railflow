from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from models import Booking
from services.booking_service import create_booking, cancel_booking, BookingError
from services.seat_service import get_seat_map

bookings_bp = Blueprint("bookings", __name__, url_prefix="/api/bookings")


@bookings_bp.route("", methods=["POST"])
@jwt_required()
def create():
    uid = int(get_jwt_identity())
    try:
        booking = create_booking(uid, request.get_json() or {})
    except BookingError as e:
        return jsonify({"error": e.message}), e.status
    return jsonify({"booking": booking.to_dict(detailed=True)}), 201


@bookings_bp.route("/my", methods=["GET"])
@jwt_required()
def my_bookings():
    uid = int(get_jwt_identity())
    rows = (Booking.query.filter_by(user_id=uid)
            .order_by(Booking.booked_at.desc()).all())
    return jsonify({"bookings": [b.to_dict() for b in rows]})


@bookings_bp.route("/<int:bid>", methods=["GET"])
@jwt_required()
def get_booking(bid):
    uid = int(get_jwt_identity())
    role = get_jwt().get("role")
    b = Booking.query.get(bid)
    if not b:
        return jsonify({"error": "Booking not found"}), 404
    if role != "ADMIN" and b.user_id != uid:
        return jsonify({"error": "Forbidden"}), 403
    return jsonify({"booking": b.to_dict(detailed=True)})


@bookings_bp.route("/<int:bid>/cancel", methods=["POST"])
@jwt_required()
def cancel(bid):
    uid = int(get_jwt_identity())
    role = get_jwt().get("role")
    try:
        booking = cancel_booking(bid, user_id=uid, is_admin=(role == "ADMIN"))
    except BookingError as e:
        return jsonify({"error": e.message}), e.status
    return jsonify({"booking": booking.to_dict(detailed=True)})


@bookings_bp.route("/seatmap", methods=["GET"])
def seatmap():
    train_id = request.args.get("train_id")
    journey_date = request.args.get("date")
    class_name = request.args.get("class")
    if not (train_id and journey_date and class_name):
        return jsonify({"error": "train_id, date and class are required"}), 400
    try:
        jd = datetime.strptime(journey_date, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"error": "Invalid date"}), 400
    sm = get_seat_map(int(train_id), jd, class_name)
    if not sm:
        return jsonify({"error": "Class not found"}), 404
    return jsonify(sm)
