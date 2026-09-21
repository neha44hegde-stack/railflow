from extensions import db


class Station(db.Model):
    __tablename__ = "stations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "code": self.code,
            "city": self.city, "state": self.state,
        }
