from io import BytesIO
from flask import Blueprint, jsonify, send_file
from models import Booking

pnr_bp = Blueprint("pnr", __name__, url_prefix="/api/pnr")


@pnr_bp.route("/<pnr>", methods=["GET"])
def lookup(pnr):
    b = Booking.query.filter_by(pnr=pnr).first()
    if not b:
        return jsonify({"error": "PNR not found"}), 404
    return jsonify({"booking": b.to_dict(detailed=True)})


@pnr_bp.route("/<pnr>/qr", methods=["GET"])
def qr(pnr):
    import qrcode
    b = Booking.query.filter_by(pnr=pnr).first()
    if not b:
        return jsonify({"error": "PNR not found"}), 404
    payload = f"RAILFLOW|PNR:{b.pnr}|TRAIN:{b.train.train_number if b.train else ''}|DATE:{b.journey_date}"
    img = qrcode.make(payload)
    buf = BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png", download_name=f"{pnr}.png")
