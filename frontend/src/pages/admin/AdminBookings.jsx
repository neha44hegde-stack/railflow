import { useEffect, useState } from "react";
import api from "../../services/api";
import { Card, Empty, ErrorBox, Spinner } from "../../components/ui";

export default function AdminBookings() {
  const [bookings, setBookings] = useState(null);
  const [filters, setFilters] = useState({ pnr: "", status: "", journey_date: "" });
  const [err, setErr] = useState("");

  const load = () => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => v && params.set(k, v));
    return api.get(`/admin/bookings?${params.toString()}`)
      .then((r) => setBookings(r.data.bookings))
      .catch((e) => setErr(e?.response?.data?.error || "Load failed"));
  };
  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-navy-900">All Bookings</h1>
      <Card className="p-4">
        <div className="grid md:grid-cols-4 gap-2">
          <input placeholder="PNR" value={filters.pnr} onChange={(e) => setFilters({ ...filters, pnr: e.target.value })} className="border rounded px-2 py-1" />
          <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })} className="border rounded px-2 py-1">
            <option value="">Any status</option><option>CONFIRMED</option><option>CANCELLED</option>
          </select>
          <input type="date" value={filters.journey_date} onChange={(e) => setFilters({ ...filters, journey_date: e.target.value })} className="border rounded px-2 py-1" />
          <button onClick={load} className="bg-rail-600 text-white rounded px-3 py-1">Search</button>
        </div>
      </Card>
      <ErrorBox message={err} />
      {!bookings ? <Spinner /> : bookings.length === 0 ? <Empty message="No bookings." /> : (
        <Card className="p-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-gray-500">
              <th className="py-2">PNR</th><th>Train</th><th>Journey</th><th>Route</th>
              <th>Class</th><th>Amount</th><th>Status</th>
            </tr></thead>
            <tbody>
              {bookings.map((b) => (
                <tr key={b.id} className="border-t">
                  <td className="py-2 font-mono">{b.pnr}</td>
                  <td>{b.train?.train_number}</td>
                  <td>{b.journey_date}</td>
                  <td>{b.source_station?.name} to {b.destination_station?.name}</td>
                  <td>{b.class_name}</td><td>Rs.{b.total_amount}</td>
                  <td><span className={`text-xs px-2 py-1 rounded ${b.status === "CONFIRMED" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>{b.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
