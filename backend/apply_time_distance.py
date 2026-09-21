"""Add distance_km input to admin route form + convert all times to 12-hour AM/PM."""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(os.path.dirname(ROOT), "frontend")

FILES = {}

# ---------------- time helper ----------------
FILES[os.path.join(FRONTEND, "src", "utils", "time.js")] = '''// Format "HH:MM" (24h) as "h:MM AM/PM". Returns "--" if missing.
export function format12h(t) {
  if (!t) return "--";
  const parts = String(t).split(":");
  if (parts.length < 2) return t;
  const h = parseInt(parts[0], 10);
  const m = parseInt(parts[1], 10);
  if (isNaN(h) || isNaN(m)) return t;
  const ampm = h < 12 ? "AM" : "PM";
  const h12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
  return `${h12}:${String(m).padStart(2, "0")} ${ampm}`;
}
'''

# ---------------- admin train detail ----------------
FILES[os.path.join(FRONTEND, "src", "pages", "admin", "AdminTrainDetail.jsx")] = '''import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "../../services/api";
import { Button, Card, Empty, ErrorBox, Spinner } from "../../components/ui";
import { format12h } from "../../utils/time";

export default function AdminTrainDetail() {
  const { id } = useParams();
  const [train, setTrain] = useState(null);
  const [route, setRoute] = useState([]);
  const [classes, setClasses] = useState([]);
  const [stations, setStations] = useState([]);
  const [stopForm, setStopForm] = useState({
    station_id: "", stop_number: "", arrival_time: "", departure_time: "", distance_km: "",
  });
  const [clsForm, setClsForm] = useState({
    class_name: "", total_seats: "", fare: "", seat_prefix: "S",
  });
  const [err, setErr] = useState("");

  const load = async () => {
    try {
      const [t, r, c, s] = await Promise.all([
        api.get(`/trains/${id}`),
        api.get(`/trains/${id}/route`),
        api.get(`/trains/${id}/classes`),
        api.get("/stations"),
      ]);
      setTrain(t.data.train);
      setRoute(r.data.route);
      setClasses(c.data.classes);
      setStations(s.data.stations);
    } catch (e) { setErr(e?.response?.data?.error || "Load failed"); }
  };
  useEffect(() => { load(); }, [id]);

  const addStop = async (e) => {
    e.preventDefault(); setErr("");
    try {
      await api.post(`/trains/${id}/route`, stopForm);
      setStopForm({ station_id: "", stop_number: "", arrival_time: "", departure_time: "", distance_km: "" });
      load();
    } catch (ex) { setErr(ex?.response?.data?.error || "Add stop failed"); }
  };

  const delStop = async (rid) => {
    if (!confirm("Remove stop?")) return;
    try { await api.delete(`/trains/${id}/route/${rid}`); load(); }
    catch (ex) { setErr(ex?.response?.data?.error || "Delete failed"); }
  };

  const addClass = async (e) => {
    e.preventDefault(); setErr("");
    try {
      await api.post(`/trains/${id}/classes`, clsForm);
      setClsForm({ class_name: "", total_seats: "", fare: "", seat_prefix: "S" });
      load();
    } catch (ex) { setErr(ex?.response?.data?.error || "Add class failed"); }
  };

  const delClass = async (cid) => {
    if (!confirm("Delete class?")) return;
    try { await api.delete(`/trains/${id}/classes/${cid}`); load(); }
    catch (ex) { setErr(ex?.response?.data?.error || "Delete failed"); }
  };

  if (!train) return <Spinner />;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-navy-900">
        {train.train_number} - {train.train_name}
      </h1>
      <ErrorBox message={err} />

      <Card className="p-4">
        <h2 className="font-semibold mb-3">Route</h2>
        <form onSubmit={addStop} className="grid md:grid-cols-7 gap-2 items-end mb-3">
          <select
            required
            value={stopForm.station_id}
            onChange={(e) => setStopForm({ ...stopForm, station_id: e.target.value })}
            className="border rounded px-2 py-1 md:col-span-2"
          >
            <option value="">Station</option>
            {stations.map((s) => (
              <option key={s.id} value={s.id}>{s.name} ({s.code})</option>
            ))}
          </select>
          <input
            type="number"
            placeholder="Stop #"
            required
            value={stopForm.stop_number}
            onChange={(e) => setStopForm({ ...stopForm, stop_number: e.target.value })}
            className="border rounded px-2 py-1"
          />
          <input
            type="number"
            placeholder="Distance km"
            value={stopForm.distance_km}
            onChange={(e) => setStopForm({ ...stopForm, distance_km: e.target.value })}
            className="border rounded px-2 py-1"
            title="Kilometres from origin (0 for first stop)"
          />
          <input
            placeholder="Arrival HH:MM"
            value={stopForm.arrival_time}
            onChange={(e) => setStopForm({ ...stopForm, arrival_time: e.target.value })}
            className="border rounded px-2 py-1"
            title="24-hour format, e.g. 17:30"
          />
          <input
            placeholder="Departure HH:MM"
            value={stopForm.departure_time}
            onChange={(e) => setStopForm({ ...stopForm, departure_time: e.target.value })}
            className="border rounded px-2 py-1"
            title="24-hour format, e.g. 06:00"
          />
          <Button type="submit">Add Stop</Button>
        </form>
        <p className="text-xs text-gray-500 mb-3">
          Type time as 24-hour HH:MM (e.g. 06:00 or 17:30) — it will display as 6:00 AM / 5:30 PM in the route and search.
        </p>
        {route.length === 0 ? <Empty message="No stops yet." /> : (
          <ol className="space-y-1">
            {route.map((s) => (
              <li key={s.id} className="flex items-center justify-between border rounded p-2 text-sm">
                <span>
                  <b>{s.stop_number}. {s.station?.name}</b>
                  <span className="text-gray-500 ml-3">
                    arr {format12h(s.arrival_time)} | dep {format12h(s.departure_time)}
                    {s.distance_km ? ` | ${s.distance_km} km` : ""}
                  </span>
                </span>
                <button onClick={() => delStop(s.id)} className="text-red-600">Remove</button>
              </li>
            ))}
          </ol>
        )}
      </Card>

      <Card className="p-4">
        <h2 className="font-semibold mb-3">Classes & Fares</h2>
        <form onSubmit={addClass} className="grid md:grid-cols-5 gap-2 items-end mb-3">
          <input
            placeholder="Class name"
            required
            value={clsForm.class_name}
            onChange={(e) => setClsForm({ ...clsForm, class_name: e.target.value })}
            className="border rounded px-2 py-1"
          />
          <input
            type="number"
            placeholder="Total seats"
            required
            value={clsForm.total_seats}
            onChange={(e) => setClsForm({ ...clsForm, total_seats: e.target.value })}
            className="border rounded px-2 py-1"
          />
          <input
            type="number"
            step="0.01"
            placeholder="Fare (base)"
            required
            value={clsForm.fare}
            onChange={(e) => setClsForm({ ...clsForm, fare: e.target.value })}
            className="border rounded px-2 py-1"
          />
          <input
            placeholder="Seat prefix"
            value={clsForm.seat_prefix}
            onChange={(e) => setClsForm({ ...clsForm, seat_prefix: e.target.value })}
            className="border rounded px-2 py-1"
          />
          <Button type="submit">Add Class</Button>
        </form>
        <p className="text-xs text-gray-500 mb-3">
          Fare is per 100 km if distances are set on the route. Otherwise it is used as a flat fare.
        </p>
        {classes.length === 0 ? <Empty message="No classes yet." /> : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500">
                <th className="py-2">Class</th><th>Seats</th><th>Fare</th><th>Prefix</th><th></th>
              </tr>
            </thead>
            <tbody>
              {classes.map((c) => (
                <tr key={c.id} className="border-t">
                  <td className="py-2">{c.class_name}</td>
                  <td>{c.total_seats}</td>
                  <td>Rs.{c.fare}</td>
                  <td>{c.seat_prefix}</td>
                  <td>
                    <button onClick={() => delClass(c.id)} className="text-red-600">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
'''

# ---------------- search page ----------------
FILES[os.path.join(FRONTEND, "src", "pages", "SearchPage.jsx")] = '''import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { Button, Card, Empty, ErrorBox, Spinner } from "../components/ui";
import { format12h } from "../utils/time";

const CLASSES = ["", "Sleeper", "AC 3 Tier", "AC 2 Tier", "AC 1 Tier", "Chair Car"];
const TYPES = ["", "Express", "Superfast", "Intercity", "Passenger", "Other"];

export default function SearchPage() {
  const nav = useNavigate();
  const [stations, setStations] = useState([]);
  const [form, setForm] = useState({
    source: "", destination: "",
    date: new Date(Date.now() + 86400000).toISOString().slice(0, 10),
    class: "", train_type: "",
  });
  const [results, setResults] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.get("/stations").then((r) => setStations(r.data.stations)); }, []);

  const search = async (e) => {
    e.preventDefault();
    setErr(""); setBusy(true); setResults(null);
    try {
      const params = new URLSearchParams();
      params.set("source", form.source);
      params.set("destination", form.destination);
      if (form.date) params.set("date", form.date);
      if (form.class) params.set("class", form.class);
      if (form.train_type) params.set("train_type", form.train_type);
      const r = await api.get(`/trains/search?${params.toString()}`);
      setResults(r.data.trains);
    } catch (ex) {
      setErr(ex?.response?.data?.error || "Search failed");
    } finally { setBusy(false); }
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h1 className="text-xl font-bold text-navy-900 mb-4">Search Trains</h1>
        <form onSubmit={search} className="grid md:grid-cols-6 gap-3">
          <select required value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })}
                  className="border border-gray-300 rounded-md px-3 py-2 md:col-span-1">
            <option value="">From</option>
            {stations.map((s) => <option key={s.id} value={s.id}>{s.name} ({s.code})</option>)}
          </select>
          <select required value={form.destination} onChange={(e) => setForm({ ...form, destination: e.target.value })}
                  className="border border-gray-300 rounded-md px-3 py-2 md:col-span-1">
            <option value="">To</option>
            {stations.map((s) => <option key={s.id} value={s.id}>{s.name} ({s.code})</option>)}
          </select>
          <input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })}
                 className="border border-gray-300 rounded-md px-3 py-2 md:col-span-1" />
          <select value={form.class} onChange={(e) => setForm({ ...form, class: e.target.value })}
                  className="border border-gray-300 rounded-md px-3 py-2 md:col-span-1">
            {CLASSES.map((c) => <option key={c} value={c}>{c || "Any class"}</option>)}
          </select>
          <select value={form.train_type} onChange={(e) => setForm({ ...form, train_type: e.target.value })}
                  className="border border-gray-300 rounded-md px-3 py-2 md:col-span-1">
            {TYPES.map((t) => <option key={t} value={t}>{t || "Any type"}</option>)}
          </select>
          <Button type="submit" disabled={busy}>{busy ? "Searching..." : "Search"}</Button>
        </form>
      </Card>

      <ErrorBox message={err} />
      {busy && <Spinner label="Searching trains..." />}

      {results && results.length === 0 && (
        <Empty message="No trains found for this route and date." />
      )}

      {results && results.length > 0 && (
        <div className="space-y-4">
          {results.map((r) => (
            <Card key={r.train.id} className="p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="font-bold text-navy-900">
                    {r.train.train_number} - {r.train.train_name}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    {r.source.station.name}{" "}
                    <span className="text-gray-500">(dep {format12h(r.departure)})</span>
                    <span className="mx-2 text-gray-400">-&gt;</span>
                    {r.destination.station.name}{" "}
                    <span className="text-gray-500">(arr {format12h(r.arrival)})</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {r.train.train_type}
                    {r.distance_km > 0 ? ` | ${r.distance_km} km` : ""}
                  </div>
                </div>
                <div className="flex flex-wrap gap-3">
                  {r.classes.map((c) => (
                    <div key={c.class_name} className="text-right border border-gray-200 rounded-md px-3 py-2">
                      <div className="text-sm font-medium">{c.class_name}</div>
                      <div className="text-xs text-gray-500">
                        Rs.{c.fare} | {c.available_seats} left
                      </div>
                    </div>
                  ))}
                </div>
                <Button onClick={() => {
                  const params = new URLSearchParams({
                    source: r.source.station.id,
                    destination: r.destination.station.id,
                    date: form.date,
                    class: form.class || "Sleeper",
                  });
                  nav(`/book/${r.train.id}?${params.toString()}`);
                }}>Book</Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
'''

# ---------------- bookings page ----------------
FILES[os.path.join(FRONTEND, "src", "pages", "MyBookings.jsx")] = '''import { useEffect, useState } from "react";
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
'''

print("Writing files...")
for path, content in FILES.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("  ", os.path.relpath(path, FRONTEND))

print("\nDone.")
print("Restart the frontend (Ctrl+C in pnpm terminal, then: pnpm dev)")