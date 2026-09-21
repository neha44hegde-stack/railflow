from datetime import datetime, date
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
