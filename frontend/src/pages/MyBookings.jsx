import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";
import { Card, Button, Empty, ErrorBox, Spinner } from "../components/ui";

export default function MyBookings() {
  const [bookings, setBookings] = useState(null);
  const [tab, setTab] = useState("UPCOMING");
  const [err, setErr] = useState("");

  const load = () => {
    api.get("/bookings/my")
      .then((r) => setBookings(r.data.bookings))
      .catch((e) => setErr(e?.response?.data?.error || "Failed to load"));
  };
  useEffect(load, []);

  const cancel = async (id) => {
    if (!confirm("Cancel this booking?")) return;
    try { await api.post(`/bookings/${id}/cancel`); load(); }
    catch (e) { alert(e?.response?.data?.error || "Cancel failed"); }
  };

  if (bookings === null) return <Spinner />;

  const today = new Date().toISOString().slice(0, 10);
  const filtered = bookings.filter((b) => {
    if (tab === "UPCOMING")  return b.status === "CONFIRMED" && b.journey_date >= today;
    if (tab === "COMPLETED") return b.status === "CONFIRMED" && b.journey_date < today;
    return b.status === "CANCELLED";
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-navy-900">My Bookings</h1>
      <div className="flex gap-2">
        {["UPCOMING", "COMPLETED", "CANCELLED"].map((t) => (
          <button key={t} onClick={() => setTab(t)}
                  className={`px-3 py-2 text-sm rounded-md ${tab === t ? "bg-navy-900 text-white" : "bg-gray-100"}`}>
            {t}
          </button>
        ))}
      </div>
      <ErrorBox message={err} />
      {filtered.length === 0 && <Empty message="No bookings in this section." />}
      <div className="space-y-3">
        {filtered.map((b) => (
          <Card key={b.id} className="p-4">
            <div className="flex justify-between flex-wrap gap-3">
              <div>
                <div className="font-bold text-navy-900 flex items-center gap-2">
                  {b.pnr}
                  {b.booking_status === "WL" && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
                      WL{b.waitlist_position}
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-700">{b.train?.train_number} - {b.train?.train_name}</div>
                <div className="text-sm text-gray-600">
                  {b.source_station?.name} to {b.destination_station?.name} - {b.journey_date}
                </div>
                <div className="text-sm text-gray-600">{b.class_name} - Rs.{b.total_amount}</div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 text-xs rounded ${b.status === "CONFIRMED" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                  {b.status}
                </span>
                <Link to={`/ticket/${b.pnr}`} className="text-rail-600 text-sm hover:underline">View Ticket</Link>
                {b.status === "CONFIRMED" && b.journey_date >= today && (
                  <Button variant="danger" onClick={() => cancel(b.id)}>Cancel</Button>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
