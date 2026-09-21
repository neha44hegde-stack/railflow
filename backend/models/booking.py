from datetime import datetime
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
