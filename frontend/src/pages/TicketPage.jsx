import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "../services/api";
import { Button, Card, ErrorBox, Spinner } from "../components/ui";

const API_BASE = "http://localhost:5000/api";

export default function TicketPage() {
  const { pnr } = useParams();
  const [booking, setBooking] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get(`/pnr/${pnr}`)
      .then((r) => setBooking(r.data.booking))
      .catch((e) => setErr(e?.response?.data?.error || "Failed"));
  }, [pnr]);

  if (err) return <ErrorBox message={err} />;
  if (!booking) return <Spinner />;

  const statusLabel = booking.booking_status === "WL"
    ? `WL${booking.waitlist_position || ""}`
    : booking.booking_status || "CNF";

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => window.print()}>Print Ticket</Button>
      </div>
      <Card className="p-6 print:shadow-none">
        <div className="border-b pb-3 mb-4 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-navy-900">RAILFLOW</h1>
            <p className="text-sm text-gray-600">E-Ticket - Not a real railway ticket</p>
          </div>
          <img
            src={`${API_BASE}/pnr/${booking.pnr}/qr`}
            alt="QR"
            width={96}
            height={96}
            className="border border-gray-200 rounded"
          />
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="space-y-1">
            <Row label="PNR" value={booking.pnr} />
            <Row label="Status" value={statusLabel} />
            <Row label="Train" value={`${booking.train?.train_number} - ${booking.train?.train_name}`} />
            <Row label="Journey Date" value={booking.journey_date} />
            <Row label="From" value={booking.source_station?.name} />
            <Row label="To" value={booking.destination_station?.name} />
            <Row label="Class" value={booking.class_name} />
            <Row label="Total Fare" value={`Rs.${booking.total_amount}`} />
            <Row label="Booking" value={booking.status} />
          </div>
          <div>
            <h3 className="font-semibold mb-2">Passengers</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500">
                  <th className="py-1">Name</th><th>Age</th><th>Gender</th><th>Seat</th>
                </tr>
              </thead>
              <tbody>
                {booking.passengers.map((p) => (
                  <tr key={p.id} className="border-t">
                    <td className="py-1">{p.name}</td><td>{p.age}</td>
                    <td>{p.gender}</td>
                    <td className={booking.booking_status === "WL" ? "text-amber-700 font-semibold" : ""}>
                      {p.seat_number}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Card>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between border-b border-dashed py-1 text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
