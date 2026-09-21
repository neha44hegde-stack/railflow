import { useEffect, useState } from "react";
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
