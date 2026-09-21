from extensions import db


class Train(db.Model):
    __tablename__ = "trains"

    id = db.Column(db.Integer, primary_key=True)
    train_number = db.Column(db.String(10), unique=True, nullable=False, index=True)
    train_name = db.Column(db.String(150), nullable=False)
    train_type = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")

    route_stops = db.relationship("TrainStation", back_populates="train",
                                  cascade="all, delete-orphan",
                                  order_by="TrainStation.stop_number")
    classes = db.relationship("TrainClass", back_populates="train", cascade="all, delete-orphan")
    bookings = db.relationship("Booking", back_populates="train")

    def to_dict(self):
        return {
            "id": self.id, "train_number": self.train_number,
            "train_name": self.train_name, "train_type": self.train_type,
            "status": self.status,
        }
