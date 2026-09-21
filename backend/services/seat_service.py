from extensions import db
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
