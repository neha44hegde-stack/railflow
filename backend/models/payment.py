from datetime import datetime
from extensions import db


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    transaction_id = db.Column(db.String(40), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="PENDING")
    paid_at = db.Column(db.DateTime, nullable=True)

    booking = db.relationship("Booking", back_populates="payments")

    def to_dict(self):
        return {
            "id": self.id, "booking_id": self.booking_id,
            "amount": float(self.amount), "transaction_id": self.transaction_id,
            "status": self.status,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
        }
