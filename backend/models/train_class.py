from extensions import db


class TrainClass(db.Model):
    __tablename__ = "train_classes"

    id = db.Column(db.Integer, primary_key=True)
    train_id = db.Column(db.Integer, db.ForeignKey("trains.id"), nullable=False)
    class_name = db.Column(db.String(30), nullable=False)
    total_seats = db.Column(db.Integer, nullable=False)
    fare = db.Column(db.Numeric(10, 2), nullable=False)
    seat_prefix = db.Column(db.String(5), nullable=False, default="S")

    train = db.relationship("Train", back_populates="classes")

    __table_args__ = (db.UniqueConstraint("train_id", "class_name", name="uq_train_class"),)

    def to_dict(self):
        return {
            "id": self.id, "train_id": self.train_id, "class_name": self.class_name,
            "total_seats": self.total_seats, "fare": float(self.fare),
            "seat_prefix": self.seat_prefix,
        }
