"""Apply RailFlow feature pack: seat map, PNR states, distance fares, QR, audit log, speed."""
import os, sqlite3, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = ROOT
FRONTEND = os.path.join(os.path.dirname(ROOT), "frontend")

# ---------- 1. Migrate existing SQLite DB ----------
db_path = os.path.join(BACKEND, "instance", "railflow_dev.db")
if os.path.exists(db_path):
    c = sqlite3.connect(db_path)
    for stmt in [
        "ALTER TABLE bookings ADD COLUMN booking_status VARCHAR(10) DEFAULT 'CNF'",
        "ALTER TABLE bookings ADD COLUMN waitlist_position INTEGER",
        "ALTER TABLE train_stations ADD COLUMN distance_km REAL DEFAULT 0",
        """CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            action VARCHAR(50) NOT NULL,
            entity VARCHAR(50) NOT NULL,
            entity_id INTEGER,
            details TEXT,
            created_at DATETIME
        )""",
    ]:
        try:
            c.execute(stmt)
            print("migrated:", stmt.split()[2] if "TABLE" not in stmt else "audit_logs")
        except sqlite3.OperationalError as e:
            print("skip:", e)
    c.commit(); c.close()
    print("DB migrated.\n")
else:
    print("No DB yet — first run will create fresh schema.\n")

FILES = {}

# ================================================================
# BACKEND
# ================================================================

FILES["models/audit_log.py"] = '''from datetime import datetime
from extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    entity = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "action": self.action,
            "entity": self.entity,
            "entity_id": self.entity_id,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
'''

FILES["models/__init__.py"] = '''from .user import User
from .station import Station
from .train import Train
from .train_station import TrainStation
from .train_class import TrainClass
from .booking import Booking
from .passenger import Passenger
from .payment import Payment
from .audit_log import AuditLog

__all__ = [
    "User", "Station", "Train", "TrainStation",
    "TrainClass", "Booking", "Passenger", "Payment", "AuditLog",
]
'''

FILES["models/booking.py"] = '''from datetime import datetime
from extensions import db


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    pnr = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    train_id = db.Column(db.Integer, db.ForeignKey("trains.id"), nullable=False)
    journey_date = db.Column(db.Date, nullable=False)
    source_station_id = db.Column(db.Integer, db.ForeignKey("stations.id"), nullable=False)
    destination_station_id = db.Column(db.Integer, db.ForeignKey("stations.id"), nullable=False)
    class_name = db.Column(db.String(30), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="CONFIRMED")
    booking_status = db.Column(db.String(10), nullable=False, default="CNF")
    waitlist_position = db.Column(db.Integer, nullable=True)
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="bookings")
    train = db.relationship("Train", back_populates="bookings")
    source_station = db.relationship("Station", foreign_keys=[source_station_id])
    destination_station = db.relationship("Station", foreign_keys=[destination_station_id])
    passengers = db.relationship("Passenger", back_populates="booking", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="booking", cascade="all, delete-orphan")

    __table_args__ = (
        db.Index("ix_bookings_train_date", "train_id", "journey_date", "class_name"),
    )

    def to_dict(self, detailed: bool = False):
        data = {
            "id": self.id, "pnr": self.pnr, "user_id": self.user_id,
            "train_id": self.train_id,
            "journey_date": self.journey_date.isoformat() if self.journey_date else None,
            "source_station_id": self.source_station_id,
            "destination_station_id": self.destination_station_id,
            "class_name": self.class_name, "total_amount": float(self.total_amount),
            "status": self.status,
            "booking_status": self.booking_status or "CNF",
            "waitlist_position": self.waitlist_position,
            "booked_at": self.booked_at.isoformat() if self.booked_at else None,
            "train": self.train.to_dict() if self.train else None,
            "source_station": self.source_station.to_dict() if self.source_station else None,
            "destination_station": self.destination_station.to_dict() if self.destination_station else None,
        }
        if detailed:
            data["passengers"] = [p.to_dict() for p in self.passengers]
            data["payments"] = [p.to_dict() for p in self.payments]
        return data
'''

FILES["models/train_station.py"] = '''from extensions import db


class TrainStation(db.Model):
    __tablename__ = "train_stations"

    id = db.Column(db.Integer, primary_key=True)
    train_id = db.Column(db.Integer, db.ForeignKey("trains.id"), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey("stations.id"), nullable=False)
    stop_number = db.Column(db.Integer, nullable=False)
    arrival_time = db.Column(db.String(5), nullable=True)
    departure_time = db.Column(db.String(5), nullable=True)
    distance_km = db.Column(db.Float, nullable=True, default=0)

    train = db.relationship("Train", back_populates="route_stops")
    station = db.relationship("Station")

    __table_args__ = (
        db.UniqueConstraint("train_id", "station_id", name="uq_train_station"),
        db.UniqueConstraint("train_id", "stop_number", name="uq_train_stop_number"),
    )

    def to_dict(self):
        return {
            "id": self.id, "train_id": self.train_id, "station_id": self.station_id,
            "stop_number": self.stop_number,
            "arrival_time": self.arrival_time, "departure_time": self.departure_time,
            "distance_km": float(self.distance_km or 0),
            "station": self.station.to_dict() if self.station else None,
        }
'''

FILES["utils/audit.py"] = '''from flask_jwt_extended import get_jwt_identity
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
'''

FILES["services/seat_service.py"] = '''from extensions import db
from models import Booking, Passenger, TrainClass


def booked_seats_count(train_id, journey_date, class_name):
    q = (
        db.session.query(db.func.count(Passenger.id))
        .join(Booking, Passenger.booking_id == Booking.id)
        .filter(
            Booking.train_id == train_id,
            Booking.journey_date == journey_date,
            Booking.class_name == class_name,
            Booking.status == "CONFIRMED",
            Booking.booking_status == "CNF",
        )
    )
    return int(q.scalar() or 0)


def available_seats(train_id, journey_date, class_name):
    tc = TrainClass.query.filter_by(train_id=train_id, class_name=class_name).first()
    if not tc:
        return 0, 0, 0
    booked = booked_seats_count(train_id, journey_date, class_name)
    available = max(tc.total_seats - booked, 0)
    return tc.total_seats, booked, available


def allocate_seats(train_id, journey_date, class_name, count):
    tc = TrainClass.query.filter_by(train_id=train_id, class_name=class_name).first()
    if not tc:
        return None
    booked = booked_seats_count(train_id, journey_date, class_name)
    if booked + count > tc.total_seats:
        return None
    return [f"{tc.seat_prefix}{booked + i + 1}" for i in range(count)]


def get_seat_map(train_id, journey_date, class_name):
    tc = TrainClass.query.filter_by(train_id=train_id, class_name=class_name).first()
    if not tc:
        return None
    taken = set()
    rows = (
        db.session.query(Passenger.seat_number)
        .join(Booking, Passenger.booking_id == Booking.id)
        .filter(
            Booking.train_id == train_id,
            Booking.journey_date == journey_date,
            Booking.class_name == class_name,
            Booking.status == "CONFIRMED",
            Booking.booking_status == "CNF",
        ).all()
    )
    for (sn,) in rows:
        if sn:
            taken.add(sn)
    seats = []
    for i in range(tc.total_seats):
        num = f"{tc.seat_prefix}{i + 1}"
        seats.append({"number": num, "booked": num in taken})
    return {
        "class_name": class_name,
        "prefix": tc.seat_prefix,
        "total_seats": tc.total_seats,
        "columns": 4,
        "seats": seats,
    }
'''

FILES["services/booking_service.py"] = '''from datetime import datetime, date
from extensions import db
from models import Booking, Passenger, Payment, Train, TrainStation, TrainClass
from services.seat_service import available_seats, allocate_seats
from services.pnr_service import generate_pnr


class BookingError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


ALLOWED_GENDERS = {"MALE", "FEMALE", "OTHER"}


def _per_passenger_fare(tc, src, dst):
    """Distance-based fare if distances set; else flat fare."""
    try:
        s = float(src.distance_km or 0)
        d = float(dst.distance_km or 0)
        if s > 0 or d > 0:
            dist = max(d - s, 1)
            # fare is treated as per-100km base; scale by distance
            return float(tc.fare) * (dist / 100.0)
    except Exception:
        pass
    return float(tc.fare)


def create_booking(user_id, payload):
    for field in ("train_id", "journey_date", "source_station_id",
                  "destination_station_id", "class_name", "passengers"):
        if field not in payload:
            raise BookingError(f"Missing field: {field}", 400)

    try:
        jd = datetime.strptime(payload["journey_date"], "%Y-%m-%d").date()
    except Exception:
        raise BookingError("Invalid journey_date format (YYYY-MM-DD)", 400)

    if jd < date.today():
        raise BookingError("Journey date cannot be in the past", 400)

    passengers_in = payload["passengers"]
    if not isinstance(passengers_in, list) or not passengers_in:
        raise BookingError("At least one passenger is required", 400)
    if len(passengers_in) > 6:
        raise BookingError("Maximum 6 passengers per booking", 400)

    for p in passengers_in:
        if not str(p.get("name", "")).strip():
            raise BookingError("Passenger name required", 400)
        try:
            age = int(p.get("age"))
        except Exception:
            raise BookingError("Passenger age must be a number", 400)
        if age < 1 or age > 120:
            raise BookingError("Passenger age must be 1-120", 400)
        if p.get("gender") not in ALLOWED_GENDERS:
            raise BookingError("Invalid gender", 400)

    train = Train.query.get(payload["train_id"])
    if not train or train.status != "ACTIVE":
        raise BookingError("Train not available", 404)

    src = TrainStation.query.filter_by(train_id=train.id, station_id=payload["source_station_id"]).first()
    dst = TrainStation.query.filter_by(train_id=train.id, station_id=payload["destination_station_id"]).first()
    if not src or not dst:
        raise BookingError("Station not on train route", 400)
    if src.stop_number >= dst.stop_number:
        raise BookingError("Source must be before destination on the route", 400)

    tc = TrainClass.query.filter_by(train_id=train.id, class_name=payload["class_name"]).first()
    if not tc:
        raise BookingError("Invalid class for this train", 400)

    try:
        _, _, avail = available_seats(train.id, jd, tc.class_name)
        want = len(passengers_in)

        per_pax = _per_passenger_fare(tc, src, dst)
        total_amount = round(per_pax * want, 2)

        booking = Booking(
            pnr=generate_pnr(), user_id=user_id, train_id=train.id, journey_date=jd,
            source_station_id=src.station_id, destination_station_id=dst.station_id,
            class_name=tc.class_name, total_amount=total_amount, status="CONFIRMED",
            booking_status="CNF",
        )

        if avail >= want:
            seats = allocate_seats(train.id, jd, tc.class_name, want)
            if not seats:
                raise BookingError("Could not allocate seats", 409)
            db.session.add(booking)
            db.session.flush()
            for p, seat in zip(passengers_in, seats):
                db.session.add(Passenger(
                    booking_id=booking.id, name=str(p["name"]).strip(),
                    age=int(p["age"]), gender=p["gender"], seat_number=seat,
                ))
        else:
            wl_count = (
                db.session.query(db.func.count(Booking.id))
                .filter(
                    Booking.train_id == train.id,
                    Booking.journey_date == jd,
                    Booking.class_name == tc.class_name,
                    Booking.booking_status == "WL",
                    Booking.status == "CONFIRMED",
                ).scalar() or 0
            )
            booking.booking_status = "WL"
            booking.waitlist_position = int(wl_count) + 1
            db.session.add(booking)
            db.session.flush()
            for i, p in enumerate(passengers_in):
                db.session.add(Passenger(
                    booking_id=booking.id, name=str(p["name"]).strip(),
                    age=int(p["age"]), gender=p["gender"],
                    seat_number=f"WL{booking.waitlist_position + i}",
                ))

        db.session.add(Payment(
            booking_id=booking.id, amount=total_amount,
            transaction_id=f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{booking.id}",
            status="SUCCESS", paid_at=datetime.utcnow(),
        ))

        db.session.commit()
        return booking
    except BookingError:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        raise BookingError(f"Booking failed: {e}", 500)


def _promote_next_waitlisted(train_id, journey_date, class_name):
    """After a cancellation, promote the earliest WL booking to CNF and assign seats."""
    _, _, avail = available_seats(train_id, journey_date, class_name)
    if avail <= 0:
        return
    wl = (
        Booking.query
        .filter_by(train_id=train_id, journey_date=journey_date,
                   class_name=class_name, booking_status="WL", status="CONFIRMED")
        .order_by(Booking.waitlist_position.asc())
        .first()
    )
    if not wl:
        return
    n = len(wl.passengers)
    if n > avail:
        return
    seats = allocate_seats(train_id, journey_date, class_name, n)
    if not seats:
        return
    for p, seat in zip(wl.passengers, seats):
        p.seat_number = seat
    wl.booking_status = "CNF"
    wl.waitlist_position = None


def cancel_booking(booking_id, user_id=None, is_admin=False):
    booking = Booking.query.get(booking_id)
    if not booking:
        raise BookingError("Booking not found", 404)
    if not is_admin and booking.user_id != user_id:
        raise BookingError("Forbidden", 403)
    if booking.status == "CANCELLED":
        raise BookingError("Booking already cancelled", 409)

    try:
        was_cnf = booking.booking_status == "CNF"
        booking.status = "CANCELLED"
        for p in booking.payments:
            if p.status == "SUCCESS":
                p.status = "REFUNDED"
        if was_cnf:
            db.session.flush()
            _promote_next_waitlisted(booking.train_id, booking.journey_date, booking.class_name)
        db.session.commit()
        return booking
    except Exception as e:
        db.session.rollback()
        raise BookingError(f"Cancellation failed: {e}", 500)
'''

FILES["routes/bookings.py"] = '''from flask import Blueprint, request, jsonify
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
'''

FILES["routes/pnr.py"] = '''from io import BytesIO
from flask import Blueprint, jsonify, send_file
from models import Booking

pnr_bp = Blueprint("pnr", __name__, url_prefix="/api/pnr")


@pnr_bp.route("/<pnr>", methods=["GET"])
def lookup(pnr):
    b = Booking.query.filter_by(pnr=pnr).first()
    if not b:
        return jsonify({"error": "PNR not found"}), 404
    return jsonify({"booking": b.to_dict(detailed=True)})


@pnr_bp.route("/<pnr>/qr", methods=["GET"])
def qr(pnr):
    import qrcode
    b = Booking.query.filter_by(pnr=pnr).first()
    if not b:
        return jsonify({"error": "PNR not found"}), 404
    payload = f"RAILFLOW|PNR:{b.pnr}|TRAIN:{b.train.train_number if b.train else ''}|DATE:{b.journey_date}"
    img = qrcode.make(payload)
    buf = BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png", download_name=f"{pnr}.png")
'''

FILES["routes/admin.py"] = '''from datetime import date, datetime, timedelta
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
'''

FILES["routes/stations.py"] = '''from flask import Blueprint, request, jsonify
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
'''

FILES["routes/trains.py"] = '''from flask import Blueprint, request, jsonify
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
'''

FILES["routes/search.py"] = '''from datetime import datetime
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
'''

# ================================================================
# FRONTEND
# ================================================================

FILES_ABS = {}

FILES_ABS[os.path.join(FRONTEND, "vite.config.js")] = '''import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
          charts: ["recharts"],
        },
      },
    },
  },
});
'''

FILES_ABS[os.path.join(FRONTEND, "src", "App.jsx")] = '''import { lazy, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import SearchPage from "./pages/SearchPage";
import BookingPage from "./pages/BookingPage";
import MyBookings from "./pages/MyBookings";
import PnrStatus from "./pages/PnrStatus";
import TicketPage from "./pages/TicketPage";
import Profile from "./pages/Profile";

const AdminDashboard = lazy(() => import("./pages/admin/AdminDashboard"));
const AdminStations = lazy(() => import("./pages/admin/AdminStations"));
const AdminTrains = lazy(() => import("./pages/admin/AdminTrains"));
const AdminTrainDetail = lazy(() => import("./pages/admin/AdminTrainDetail"));
const AdminBookings = lazy(() => import("./pages/admin/AdminBookings"));
const AdminUsers = lazy(() => import("./pages/admin/AdminUsers"));
const AdminAuditLog = lazy(() => import("./pages/admin/AdminAuditLog"));

const Fallback = () => <div className="p-8 text-gray-500 text-center text-sm">Loading...</div>;

export default function App() {
  return (
    <Layout>
      <Suspense fallback={<Fallback />}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route path="/search" element={<ProtectedRoute role="PASSENGER"><SearchPage /></ProtectedRoute>} />
          <Route path="/book/:trainId" element={<ProtectedRoute role="PASSENGER"><BookingPage /></ProtectedRoute>} />
          <Route path="/bookings" element={<ProtectedRoute role="PASSENGER"><MyBookings /></ProtectedRoute>} />
          <Route path="/pnr" element={<PnrStatus />} />
          <Route path="/ticket/:pnr" element={<ProtectedRoute><TicketPage /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />

          <Route path="/admin" element={<ProtectedRoute role="ADMIN"><AdminDashboard /></ProtectedRoute>} />
          <Route path="/admin/stations" element={<ProtectedRoute role="ADMIN"><AdminStations /></ProtectedRoute>} />
          <Route path="/admin/trains" element={<ProtectedRoute role="ADMIN"><AdminTrains /></ProtectedRoute>} />
          <Route path="/admin/trains/:id" element={<ProtectedRoute role="ADMIN"><AdminTrainDetail /></ProtectedRoute>} />
          <Route path="/admin/bookings" element={<ProtectedRoute role="ADMIN"><AdminBookings /></ProtectedRoute>} />
          <Route path="/admin/users" element={<ProtectedRoute role="ADMIN"><AdminUsers /></ProtectedRoute>} />
          <Route path="/admin/audit" element={<ProtectedRoute role="ADMIN"><AdminAuditLog /></ProtectedRoute>} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </Layout>
  );
}
'''

FILES_ABS[os.path.join(FRONTEND, "src", "components", "Layout.jsx")] = '''import { Link, NavLink, useNavigate } from "react-router-dom";
import { Train, LogOut, FileText } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const nav = useNavigate();

  const linkCls = ({ isActive }) =>
    `px-3 py-2 rounded-md text-sm font-medium ${isActive ? "bg-navy-800 text-white" : "text-gray-700 hover:bg-gray-100"}`;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-navy-900 text-white">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-lg font-bold">
            <Train size={22} /> RAILFLOW
          </Link>
          <nav className="flex items-center gap-2">
            {user ? (
              <>
                {user.role === "PASSENGER" && (
                  <>
                    <NavLink to="/search" className={linkCls}>Search</NavLink>
                    <NavLink to="/bookings" className={linkCls}>My Bookings</NavLink>
                    <NavLink to="/pnr" className={linkCls}>PNR Status</NavLink>
                  </>
                )}
                {user.role === "ADMIN" && (
                  <>
                    <NavLink to="/admin" end className={linkCls}>Dashboard</NavLink>
                    <NavLink to="/admin/stations" className={linkCls}>Stations</NavLink>
                    <NavLink to="/admin/trains" className={linkCls}>Trains</NavLink>
                    <NavLink to="/admin/bookings" className={linkCls}>Bookings</NavLink>
                    <NavLink to="/admin/users" className={linkCls}>Users</NavLink>
                    <NavLink to="/admin/audit" className={linkCls}>
                      <span className="inline-flex items-center gap-1"><FileText size={14}/>Audit</span>
                    </NavLink>
                  </>
                )}
                <span className="text-sm text-gray-300 ml-2">{user.name}</span>
                <button onClick={() => { logout(); nav("/login"); }}
                        className="ml-2 text-gray-300 hover:text-white" title="Logout">
                  <LogOut size={18} />
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="px-3 py-2 text-sm hover:bg-navy-800 rounded-md">Login</Link>
                <Link to="/register" className="px-3 py-2 text-sm bg-rail-600 hover:bg-rail-500 rounded-md">Register</Link>
              </>
            )}
          </nav>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
'''

FILES_ABS[os.path.join(FRONTEND, "src", "pages", "TicketPage.jsx")] = '''import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "../services/api";
import { Button, Card, ErrorBox, Spinner } from "../components/ui";

const API_BASE = "http://localhost:5000/api";

export default function TicketPage() {
  const { pnr } = useParams();
  const [booking, setBooking] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get(`/pnr/${pnr}`)
      .then((r) => setBooking(r.data.booking))
      .catch((e) => setErr(e?.response?.data?.error || "Failed"));
  }, [pnr]);

  if (err) return <ErrorBox message={err} />;
  if (!booking) return <Spinner />;

  const statusLabel = booking.booking_status === "WL"
    ? `WL${booking.waitlist_position || ""}`
    : booking.booking_status || "CNF";

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => window.print()}>Print Ticket</Button>
      </div>
      <Card className="p-6 print:shadow-none">
        <div className="border-b pb-3 mb-4 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-navy-900">RAILFLOW</h1>
            <p className="text-sm text-gray-600">E-Ticket - Not a real railway ticket</p>
          </div>
          <img
            src={`${API_BASE}/pnr/${booking.pnr}/qr`}
            alt="QR"
            width={96}
            height={96}
            className="border border-gray-200 rounded"
          />
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="space-y-1">
            <Row label="PNR" value={booking.pnr} />
            <Row label="Status" value={statusLabel} />
            <Row label="Train" value={`${booking.train?.train_number} - ${booking.train?.train_name}`} />
            <Row label="Journey Date" value={booking.journey_date} />
            <Row label="From" value={booking.source_station?.name} />
            <Row label="To" value={booking.destination_station?.name} />
            <Row label="Class" value={booking.class_name} />
            <Row label="Total Fare" value={`Rs.${booking.total_amount}`} />
            <Row label="Booking" value={booking.status} />
          </div>
          <div>
            <h3 className="font-semibold mb-2">Passengers</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500">
                  <th className="py-1">Name</th><th>Age</th><th>Gender</th><th>Seat</th>
                </tr>
              </thead>
              <tbody>
                {booking.passengers.map((p) => (
                  <tr key={p.id} className="border-t">
                    <td className="py-1">{p.name}</td><td>{p.age}</td>
                    <td>{p.gender}</td>
                    <td className={booking.booking_status === "WL" ? "text-amber-700 font-semibold" : ""}>
                      {p.seat_number}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Card>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between border-b border-dashed py-1 text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
'''

FILES_ABS[os.path.join(FRONTEND, "src", "pages", "BookingPage.jsx")] = '''import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import api from "../services/api";
import { Button, Card, ErrorBox, Spinner } from "../components/ui";

export default function BookingPage() {
  const { trainId } = useParams();
  const [sp] = useSearchParams();
  const nav = useNavigate();
  const [train, setTrain] = useState(null);
  const [classes, setClasses] = useState([]);
  const [passengers, setPassengers] = useState([{ name: "", age: "", gender: "MALE" }]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [cls, setCls] = useState(sp.get("class") || "");
  const [seatmap, setSeatmap] = useState(null);
  const [showMap, setShowMap] = useState(false);

  const source = sp.get("source");
  const destination = sp.get("destination");
  const date = sp.get("date");

  useEffect(() => {
    Promise.all([api.get(`/trains/${trainId}`), api.get(`/trains/${trainId}/classes`)])
      .then(([t, c]) => {
        setTrain(t.data.train);
        setClasses(c.data.classes);
        if (!cls && c.data.classes.length) setCls(c.data.classes[0].class_name);
      })
      .catch(() => setErr("Could not load train"));
  }, [trainId]);

  useEffect(() => {
    if (!cls || !date) { setSeatmap(null); return; }
    api.get(`/bookings/seatmap`, { params: { train_id: trainId, date, class: cls } })
      .then((r) => setSeatmap(r.data))
      .catch(() => setSeatmap(null));
  }, [cls, trainId, date]);

  const update = (i, k, v) => {
    const copy = [...passengers];
    copy[i][k] = v;
    setPassengers(copy);
  };
  const addPax = () => passengers.length < 6 && setPassengers([...passengers, { name: "", age: "", gender: "MALE" }]);
  const removePax = (i) => setPassengers(passengers.filter((_, idx) => idx !== i));

  const submit = async (e) => {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      const payload = {
        train_id: parseInt(trainId, 10),
        journey_date: date,
        source_station_id: parseInt(source, 10),
        destination_station_id: parseInt(destination, 10),
        class_name: cls,
        passengers: passengers.map((p) => ({ ...p, age: parseInt(p.age, 10) })),
      };
      const r = await api.post("/bookings", payload);
      nav(`/ticket/${r.data.booking.pnr}`);
    } catch (ex) {
      setErr(ex?.response?.data?.error || "Booking failed");
    } finally { setBusy(false); }
  };

  if (!train) return <Spinner />;
  const selected = classes.find((c) => c.class_name === cls);

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h1 className="text-xl font-bold text-navy-900">
          {train.train_number} - {train.train_name}
        </h1>
        <p className="text-sm text-gray-600">Journey date: {date}</p>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold">Class</h2>
          {seatmap && (
            <button
              type="button"
              onClick={() => setShowMap((v) => !v)}
              className="text-sm text-rail-600 hover:underline"
            >
              {showMap ? "Hide seat map" : "View seat map"}
            </button>
          )}
        </div>
        <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
          {classes.map((c) => (
            <label key={c.class_name}
                   className={`border rounded-md p-3 cursor-pointer ${cls === c.class_name ? "border-rail-600 bg-blue-50" : "border-gray-200"}`}>
              <input type="radio" name="cls" className="hidden" checked={cls === c.class_name}
                     onChange={() => setCls(c.class_name)} />
              <div className="font-medium">{c.class_name}</div>
              <div className="text-sm text-gray-600">Rs.{c.fare}</div>
            </label>
          ))}
        </div>

        {showMap && seatmap && (
          <div className="mt-4 border-t pt-4">
            <div className="flex items-center gap-4 text-xs mb-3">
              <span className="inline-flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded-sm bg-emerald-400"></span> Available
              </span>
              <span className="inline-flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded-sm bg-red-400"></span> Booked
              </span>
              <span className="text-gray-500 ml-auto">
                {seatmap.seats.filter(s => !s.booked).length} / {seatmap.total_seats} available
              </span>
            </div>
            <div
              className="grid gap-1.5 max-h-72 overflow-y-auto p-1"
              style={{ gridTemplateColumns: `repeat(${seatmap.columns}, minmax(0, 1fr))` }}
            >
              {seatmap.seats.map((s) => (
                <div
                  key={s.number}
                  title={s.number}
                  className={
                    "text-[10px] font-mono text-center rounded py-1 select-none " +
                    (s.booked
                      ? "bg-red-400 text-white"
                      : "bg-emerald-400 text-white")
                  }
                >
                  {s.number}
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      <Card className="p-6">
        <h2 className="font-semibold mb-3">Passengers</h2>
        <form onSubmit={submit} className="space-y-3">
          <ErrorBox message={err} />
          {passengers.map((p, i) => (
            <div key={i} className="grid grid-cols-12 gap-2 items-center">
              <input placeholder="Name" required value={p.name} onChange={(e) => update(i, "name", e.target.value)}
                     className="col-span-5 border border-gray-300 rounded-md px-3 py-2" />
              <input placeholder="Age" type="number" required min={1} max={120} value={p.age}
                     onChange={(e) => update(i, "age", e.target.value)}
                     className="col-span-3 border border-gray-300 rounded-md px-3 py-2" />
              <select value={p.gender} onChange={(e) => update(i, "gender", e.target.value)}
                      className="col-span-3 border border-gray-300 rounded-md px-3 py-2">
                <option value="MALE">Male</option>
                <option value="FEMALE">Female</option>
                <option value="OTHER">Other</option>
              </select>
              <button type="button" onClick={() => removePax(i)} disabled={passengers.length === 1}
                      className="col-span-1 text-red-600 text-sm disabled:opacity-40">x</button>
            </div>
          ))}
          {passengers.length < 6 && (
            <Button type="button" variant="neutral" onClick={addPax}>+ Add passenger</Button>
          )}
          <div className="border-t pt-4 flex items-center justify-between flex-wrap gap-3">
            <div className="text-sm text-gray-600">
              {selected ? <>Fare: Rs.{selected.fare} x {passengers.length} = <b>Rs.{selected.fare * passengers.length}</b></> : "Select a class"}
            </div>
            <Button type="submit" disabled={busy || !selected}>{busy ? "Booking..." : "Confirm Booking (Test Payment)"}</Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
'''

FILES_ABS[os.path.join(FRONTEND, "src", "pages", "admin", "AdminAuditLog.jsx")] = '''import { useEffect, useState } from "react";
import api from "../../services/api";
import { Card, Empty, ErrorBox, Spinner } from "../../components/ui";

export default function AdminAuditLog() {
  const [logs, setLogs] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get("/admin/audit")
      .then((r) => setLogs(r.data.logs))
      .catch((e) => setErr(e?.response?.data?.error || "Failed to load audit log"));
  }, []);

  if (err) return <ErrorBox message={err} />;
  if (!logs) return <Spinner />;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-navy-900">Audit Log</h1>
      <p className="text-sm text-gray-600">
        Every admin action is recorded here — {logs.length} entries.
      </p>
      {logs.length === 0 ? <Empty message="No audit entries yet." /> : (
        <Card className="p-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500">
                <th className="py-2">When</th>
                <th>Admin</th>
                <th>Action</th>
                <th>Entity</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id} className="border-t">
                  <td className="py-2 text-gray-600 whitespace-nowrap">
                    {l.created_at ? l.created_at.slice(0, 19).replace("T", " ") : "-"}
                  </td>
                  <td className="text-gray-900">{l.user_name || `#${l.user_id}`}</td>
                  <td>
                    <span className="px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-800 font-mono">
                      {l.action}
                    </span>
                  </td>
                  <td className="text-gray-600">
                    {l.entity}{l.entity_id ? `#${l.entity_id}` : ""}
                  </td>
                  <td className="text-gray-700">{l.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
'''

FILES_ABS[os.path.join(FRONTEND, "src", "pages", "admin", "AdminDashboard.jsx")] = '''import { useEffect, useState } from "react";
import api from "../../services/api";
import { Card, Empty, ErrorBox, Spinner } from "../../components/ui";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";

const COLORS = ["#2563eb", "#0f2a52", "#60a5fa", "#1e40af", "#93c5fd"];

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    Promise.all([api.get("/admin/dashboard"), api.get("/admin/analytics")])
      .then(([s, a]) => { setStats(s.data); setAnalytics(a.data); })
      .catch((e) => setErr(e?.response?.data?.error || "Failed to load dashboard"));
  }, []);

  if (err) return <ErrorBox message={err} />;
  if (!stats) return <Spinner />;

  const kpis = [
    ["Total Trains", stats.total_trains],
    ["Active Trains", stats.active_trains],
    ["Total Stations", stats.total_stations],
    ["Total Users", stats.total_users],
    ["Today's Bookings", stats.todays_bookings],
    ["Confirmed", stats.confirmed_bookings],
    ["Cancelled", stats.cancelled_bookings],
    ["Waitlisted", stats.waitlisted_bookings || 0],
    ["Revenue", `Rs.${stats.revenue}`],
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-navy-900">Admin Dashboard</h1>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {kpis.map(([label, v]) => (
          <Card key={label} className="p-4">
            <div className="text-xs text-gray-500">{label}</div>
            <div className="text-xl font-bold text-navy-900">{v}</div>
          </Card>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Card className="p-4">
          <h2 className="font-semibold mb-3">Bookings per day (30d)</h2>
          {analytics?.bookings_per_day?.length ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={analytics.bookings_per_day}>
                <XAxis dataKey="date" fontSize={11} />
                <YAxis fontSize={11} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          ) : <Empty message="No booking data available." />}
        </Card>

        <Card className="p-4">
          <h2 className="font-semibold mb-3">Bookings by class</h2>
          {analytics?.bookings_by_class?.length ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={analytics.bookings_by_class} dataKey="count" nameKey="class_name" outerRadius={90} label>
                  {analytics.bookings_by_class.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : <Empty message="No booking data available." />}
        </Card>

        <Card className="p-4">
          <h2 className="font-semibold mb-3">Popular trains</h2>
          {analytics?.popular_trains?.length ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={analytics.popular_trains} layout="vertical">
                <XAxis type="number" fontSize={11} allowDecimals={false} />
                <YAxis dataKey="train_number" type="category" fontSize={11} />
                <Tooltip />
                <Bar dataKey="count" fill="#0f2a52" />
              </BarChart>
            </ResponsiveContainer>
          ) : <Empty message="No booking data available." />}
        </Card>

        <Card className="p-4">
          <h2 className="font-semibold mb-3">Revenue by train</h2>
          {analytics?.revenue_by_train?.length ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={analytics.revenue_by_train}>
                <XAxis dataKey="train_number" fontSize={11} />
                <YAxis fontSize={11} />
                <Tooltip />
                <Bar dataKey="revenue" fill="#60a5fa" />
              </BarChart>
            </ResponsiveContainer>
          ) : <Empty message="No booking data available." />}
        </Card>
      </div>

      <Card className="p-4">
        <h2 className="font-semibold mb-3">Popular routes</h2>
        {analytics?.popular_routes?.length ? (
          <table className="w-full text-sm">
            <thead><tr className="text-left text-gray-500"><th className="py-1">From</th><th>To</th><th>Bookings</th></tr></thead>
            <tbody>
              {analytics.popular_routes.map((r, i) => (
                <tr key={i} className="border-t"><td className="py-1">{r.from}</td><td>{r.to}</td><td>{r.count}</td></tr>
              ))}
            </tbody>
          </table>
        ) : <Empty message="No booking data available." />}
      </Card>
    </div>
  );
}
'''

FILES_ABS[os.path.join(FRONTEND, "src", "pages", "MyBookings.jsx")] = '''import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";
import { Card, Button, Empty, ErrorBox, Spinner } from "../components/ui";

export default function MyBookings() {
  const [bookings, setBookings] = useState(null);
  const [tab, setTab] = useState("UPCOMING");
  const [err, setErr] = useState("");

  const load = () => {
    api.get("/bookings/my")
      .then((r) => setBookings(r.data.bookings))
      .catch((e) => setErr(e?.response?.data?.error || "Failed to load"));
  };
  useEffect(load, []);

  const cancel = async (id) => {
    if (!confirm("Cancel this booking?")) return;
    try { await api.post(`/bookings/${id}/cancel`); load(); }
    catch (e) { alert(e?.response?.data?.error || "Cancel failed"); }
  };

  if (bookings === null) return <Spinner />;

  const today = new Date().toISOString().slice(0, 10);
  const filtered = bookings.filter((b) => {
    if (tab === "UPCOMING")  return b.status === "CONFIRMED" && b.journey_date >= today;
    if (tab === "COMPLETED") return b.status === "CONFIRMED" && b.journey_date < today;
    return b.status === "CANCELLED";
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-navy-900">My Bookings</h1>
      <div className="flex gap-2">
        {["UPCOMING", "COMPLETED", "CANCELLED"].map((t) => (
          <button key={t} onClick={() => setTab(t)}
                  className={`px-3 py-2 text-sm rounded-md ${tab === t ? "bg-navy-900 text-white" : "bg-gray-100"}`}>
            {t}
          </button>
        ))}
      </div>
      <ErrorBox message={err} />
      {filtered.length === 0 && <Empty message="No bookings in this section." />}
      <div className="space-y-3">
        {filtered.map((b) => (
          <Card key={b.id} className="p-4">
            <div className="flex justify-between flex-wrap gap-3">
              <div>
                <div className="font-bold text-navy-900 flex items-center gap-2">
                  {b.pnr}
                  {b.booking_status === "WL" && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
                      WL{b.waitlist_position}
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-700">{b.train?.train_number} - {b.train?.train_name}</div>
                <div className="text-sm text-gray-600">
                  {b.source_station?.name} to {b.destination_station?.name} - {b.journey_date}
                </div>
                <div className="text-sm text-gray-600">{b.class_name} - Rs.{b.total_amount}</div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 text-xs rounded ${b.status === "CONFIRMED" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                  {b.status}
                </span>
                <Link to={`/ticket/${b.pnr}`} className="text-rail-600 text-sm hover:underline">View Ticket</Link>
                {b.status === "CONFIRMED" && b.journey_date >= today && (
                  <Button variant="danger" onClick={() => cancel(b.id)}>Cancel</Button>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
'''

# ================================================================
# WRITE EVERYTHING
# ================================================================

print("Writing backend files...")
for rel, content in FILES.items():
    path = os.path.join(BACKEND, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("  ", rel)

print("\nWriting frontend files...")
for path, content in FILES_ABS.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("  ", os.path.relpath(path, FRONTEND))

print("\nAll files updated. Now:")
print("  1) Restart the backend:  Ctrl+C in the backend terminal, then: python dev_frontend.py")
print("  2) Restart the frontend: Ctrl+C in the pnpm terminal,  then: pnpm dev")