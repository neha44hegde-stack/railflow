import random
from datetime import datetime
from models import Booking


def generate_pnr() -> str:
    year = datetime.utcnow().year
    for _ in range(100):
        candidate = f"RF{year}{random.randint(0, 999999):06d}"
        if not Booking.query.filter_by(pnr=candidate).first():
            return candidate
    raise RuntimeError("Could not generate unique PNR")
