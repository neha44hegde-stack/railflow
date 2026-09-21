"""Development seed. Run: python seed.py
Aborts if data already present."""
from app import create_app
from extensions import db
from models import User, Station, Train, TrainStation, TrainClass

app = create_app()

with app.app_context():
    if Station.query.count() > 0:
        print("Data already present. Aborting seed.")
        raise SystemExit(0)

    bnc = Station(name="Bengaluru City", code="BNC", city="Bengaluru", state="Karnataka")
    mdy = Station(name="Mandya", code="MDY", city="Mandya", state="Karnataka")
    mys = Station(name="Mysuru Junction", code="MYS", city="Mysuru", state="Karnataka")
    mng = Station(name="Mangaluru Central", code="MAQ", city="Mangaluru", state="Karnataka")
    db.session.add_all([bnc, mdy, mys, mng])
    db.session.flush()

    admin = User(name="Admin", email="admin@railflow.local", role="ADMIN")
    admin.set_password("admin123")
    pax = User(name="Test Passenger", email="pax@railflow.local", role="PASSENGER")
    pax.set_password("pass123")
    db.session.add_all([admin, pax])

    t = Train(train_number="12614", train_name="Bengaluru Express",
              train_type="Express", status="ACTIVE")
    db.session.add(t)
    db.session.flush()

    db.session.add_all([
        TrainStation(train_id=t.id, station_id=bnc.id, stop_number=1, arrival_time=None, departure_time="08:00"),
        TrainStation(train_id=t.id, station_id=mdy.id, stop_number=2, arrival_time="09:45", departure_time="09:47"),
        TrainStation(train_id=t.id, station_id=mys.id, stop_number=3, arrival_time="11:00", departure_time=None),
    ])

    db.session.add_all([
        TrainClass(train_id=t.id, class_name="Sleeper",   total_seats=72, fare=350,  seat_prefix="S"),
        TrainClass(train_id=t.id, class_name="AC 3 Tier", total_seats=64, fare=700,  seat_prefix="B"),
        TrainClass(train_id=t.id, class_name="AC 2 Tier", total_seats=48, fare=1000, seat_prefix="A"),
    ])

    db.session.commit()
    print("Seed complete.")
