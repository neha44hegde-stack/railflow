from datetime import date, datetime, timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from extensions import db
from models import User, Train, Station, Booking, Payment, AuditLog
from utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def dashboard():
    revenue = (db.session.query(func.coalesce(func.sum(Payment.amount), 0))
               .filter(Payment.status == "SUCCESS").scalar() or 0)
    return jsonify({
        "total_trains": Train.query.count(),
        "active_trains": Train.query.filter_by(status="ACTIVE").count(),
        "total_stations": Station.query.count(),
        "total_users": User.query.count(),
        "todays_bookings": Booking.query.filter(func.date(Booking.booked_at) == date.today()).count(),
        "confirmed_bookings": Booking.query.filter_by(status="CONFIRMED").count(),
        "cancelled_bookings": Booking.query.filter_by(status="CANCELLED").count(),
        "waitlisted_bookings": Booking.query.filter_by(booking_status="WL", status="CONFIRMED").count(),
        "revenue": float(revenue),
    })


@admin_bp.route("/analytics", methods=["GET"])
@admin_required
def analytics():
    since = datetime.utcnow() - timedelta(days=30)
    rows = (db.session.query(func.date(Booking.booked_at), func.count(Booking.id))
            .filter(Booking.booked_at >= since)
            .group_by(func.date(Booking.booked_at))
            .order_by(func.date(Booking.booked_at)).all())
    bookings_per_day = [{"date": str(r[0]), "count": int(r[1])} for r in rows]

    rows = (db.session.query(Booking.class_name, func.count(Booking.id))
            .group_by(Booking.class_name).all())
    bookings_by_class = [{"class_name": r[0], "count": int(r[1])} for r in rows]

    rows = (db.session.query(Train.train_number, Train.train_name, func.count(Booking.id))
            .join(Booking, Booking.train_id == Train.id).group_by(Train.id)
            .order_by(func.count(Booking.id).desc()).limit(10).all())
    popular_trains = [{"train_number": r[0], "train_name": r[1], "count": int(r[2])} for r in rows]

    rows = (db.session.query(Booking.source_station_id, Booking.destination_station_id,
                             func.count(Booking.id))
            .group_by(Booking.source_station_id, Booking.destination_station_id)
            .order_by(func.count(Booking.id).desc()).limit(10).all())
    popular_routes = []
    for r in rows:
        s1 = Station.query.get(r[0]); s2 = Station.query.get(r[1])
        popular_routes.append({"from": s1.name if s1 else "?",
                               "to": s2.name if s2 else "?", "count": int(r[2])})

    rows = (db.session.query(Train.train_number, func.coalesce(func.sum(Payment.amount), 0))
            .join(Booking, Booking.train_id == Train.id)
            .join(Payment, Payment.booking_id == Booking.id)
            .filter(Payment.status == "SUCCESS").group_by(Train.id)
            .order_by(func.sum(Payment.amount).desc()).limit(10).all())
    revenue_by_train = [{"train_number": r[0], "revenue": float(r[1])} for r in rows]

    return jsonify({
        "bookings_per_day": bookings_per_day,
        "bookings_by_class": bookings_by_class,
        "popular_trains": popular_trains,
        "popular_routes": popular_routes,
        "revenue_by_train": revenue_by_train,
    })


@admin_bp.route("/bookings", methods=["GET"])
@admin_required
def all_bookings():
    q = Booking.query
    pnr = request.args.get("pnr")
    status = request.args.get("status")
    train_id = request.args.get("train_id")
    journey_date = request.args.get("journey_date")
    if pnr:      q = q.filter(Booking.pnr.ilike(f"%{pnr}%"))
    if status:   q = q.filter(Booking.status == status)
    if train_id: q = q.filter(Booking.train_id == train_id)
    if journey_date:
        try:
            q = q.filter(Booking.journey_date == datetime.strptime(journey_date, "%Y-%m-%d").date())
        except Exception:
            return jsonify({"error": "Invalid journey_date"}), 400
    bookings = q.order_by(Booking.booked_at.desc()).limit(500).all()
    return jsonify({"bookings": [b.to_dict() for b in bookings]})


@admin_bp.route("/users", methods=["GET"])
@admin_required
def users():
    q = User.query
    role = request.args.get("role"); search = request.args.get("q")
    if role:   q = q.filter(User.role == role)
    if search:
        like = f"%{search}%"
        q = q.filter((User.name.ilike(like)) | (User.email.ilike(like)))
    rows = q.order_by(User.id.desc()).limit(500).all()
    result = []
    for u in rows:
        d = u.to_dict()
        d["booking_count"] = Booking.query.filter_by(user_id=u.id).count()
        result.append(d)
    return jsonify({"users": result})


@admin_bp.route("/audit", methods=["GET"])
@admin_required
def audit():
    q = AuditLog.query
    entity = request.args.get("entity")
    action = request.args.get("action")
    if entity: q = q.filter(AuditLog.entity == entity)
    if action: q = q.filter(AuditLog.action == action)
    rows = q.order_by(AuditLog.created_at.desc()).limit(300).all()
    return jsonify({"logs": [l.to_dict() for l in rows]})
