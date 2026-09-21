import { useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";
import { Button, Card, ErrorBox } from "../components/ui";

export default function PnrStatus() {
  const [pnr, setPnr] = useState("");
  const [booking, setBooking] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const lookup = async (e) => {
    e.preventDefault();
    setErr(""); setBooking(null); setBusy(true);
    try {
      const r = await api.get(`/pnr/${pnr.trim()}`);
      setBooking(r.data.booking);
    } catch (ex) {
      setErr(ex?.response?.data?.error || "Lookup failed");
    } finally { setBusy(false); }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <Card className="p-6">
        <h1 className="text-xl font-bold text-navy-900 mb-3">PNR Status</h1>
        <form onSubmit={lookup} className="flex gap-2">
          <input placeholder="Enter PNR" value={pnr} onChange={(e) => setPnr(e.target.value)} required
                 className="flex-1 border border-gray-300 rounded-md px-3 py-2" />
          <Button type="submit" disabled={busy}>{busy ? "..." : "Check"}</Button>
        </form>
        <ErrorBox message={err} />
      </Card>

      {booking && (
        <Card className="p-6 space-y-2">
          <div className="flex justify-between"><span className="text-gray-600">PNR</span><b>{booking.pnr}</b></div>
          <div className="flex justify-between"><span className="text-gray-600">Train</span><span>{booking.train?.train_number} - {booking.train?.train_name}</span></div>
          <div className="flex justify-between"><span className="text-gray-600">Journey Date</span><span>{booking.journey_date}</span></div>
          <div className="flex justify-between"><span className="text-gray-600">Route</span><span>{booking.source_station?.name} -&gt; {booking.destination_station?.name}</span></div>
          <div className="flex justify-between"><span className="text-gray-600">Class</span><span>{booking.class_name}</span></div>
          <div className="flex justify-between"><span className="text-gray-600">Amount</span><span>Rs.{booking.total_amount}</span></div>
          <div className="flex justify-between"><span className="text-gray-600">Status</span><b>{booking.status}</b></div>
          <Link to={`/ticket/${booking.pnr}`} className="text-rail-600 hover:underline text-sm">View full ticket</Link>
        </Card>
      )}
    </div>
  );
}
