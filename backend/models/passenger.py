from extensions import db


class Passenger(db.Model):
    __tablename__ = "passengers"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    seat_number = db.Column(db.String(10), nullable=False)

    booking = db.relationship("Booking", back_populates="passengers")

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "age": self.age,
            "gender": self.gender, "seat_number": self.seat_number,
        }
