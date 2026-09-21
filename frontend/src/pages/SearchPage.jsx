import { useEffect, useState } from "react";
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
