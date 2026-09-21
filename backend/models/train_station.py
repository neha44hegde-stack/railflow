from extensions import db


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
