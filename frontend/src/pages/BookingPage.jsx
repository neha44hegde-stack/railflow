import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import api from "../services/api";
import { Button, Card, ErrorBox, Spinner } from "../components/ui";

export default function BookingPage() {
  const { trainId } = useParams();
  const [sp] = useSearchParams();
  const nav = useNavigate();
  const [train, setTrain] = useState(null);
  const [classes, setClasses] = useState([]);
  const [passengers, setPassengers] = useState([{ name: "", age: "", gender: "MALE" }]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [cls, setCls] = useState(sp.get("class") || "");
  const [seatmap, setSeatmap] = useState(null);
  const [showMap, setShowMap] = useState(false);

  const source = sp.get("source");
  const destination = sp.get("destination");
  const date = sp.get("date");

  useEffect(() => {
    Promise.all([
      api.get(`/trains/${trainId}`),
      api.get(`/trains/${trainId}/classes`, { params: { source, destination } }),
    ])
      .then(([t, c]) => {
        setTrain(t.data.train);
        setClasses(c.data.classes);
        if (!cls && c.data.classes.length) setCls(c.data.classes[0].class_name);
      })
      .catch(() => setErr("Could not load train"));
  }, [trainId, source, destination]);

  useEffect(() => {
    if (!cls || !date) { setSeatmap(null); return; }
    api.get(`/bookings/seatmap`, { params: { train_id: trainId, date, class: cls } })
      .then((r) => setSeatmap(r.data))
      .catch(() => setSeatmap(null));
  }, [cls, trainId, date]);

  const update = (i, k, v) => {
    const copy = [...passengers];
    copy[i][k] = v;
    setPassengers(copy);
  };
  const addPax = () => passengers.length < 6 && setPassengers([...passengers, { name: "", age: "", gender: "MALE" }]);
  const removePax = (i) => setPassengers(passengers.filter((_, idx) => idx !== i));

  const submit = async (e) => {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      const payload = {
        train_id: parseInt(trainId, 10),
        journey_date: date,
        source_station_id: parseInt(source, 10),
        destination_station_id: parseInt(destination, 10),
        class_name: cls,
        passengers: passengers.map((p) => ({ ...p, age: parseInt(p.age, 10) })),
      };
      const r = await api.post("/bookings", payload);
      nav(`/ticket/${r.data.booking.pnr}`);
    } catch (ex) {
      setErr(ex?.response?.data?.error || "Booking failed");
    } finally { setBusy(false); }
  };

  if (!train) return <Spinner />;
  const selected = classes.find((c) => c.class_name === cls);

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h1 className="text-xl font-bold text-navy-900">
          {train.train_number} - {train.train_name}
        </h1>
        <p className="text-sm text-gray-600">Journey date: {date}</p>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold">Class</h2>
          {seatmap && (
            <button
              type="button"
              onClick={() => setShowMap((v) => !v)}
              className="text-sm text-rail-600 hover:underline"
            >
              {showMap ? "Hide seat map" : "View seat map"}
            </button>
          )}
        </div>
        <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
          {classes.map((c) => (
            <label key={c.class_name}
                   className={`border rounded-md p-3 cursor-pointer ${cls === c.class_name ? "border-rail-600 bg-blue-50" : "border-gray-200"}`}>
              <input type="radio" name="cls" className="hidden" checked={cls === c.class_name}
                     onChange={() => setCls(c.class_name)} />
              <div className="font-medium">{c.class_name}</div>
              <div className="text-sm text-gray-600">Rs.{c.fare}</div>
            </label>
          ))}
        </div>

        {showMap && seatmap && (
          <div className="mt-4 border-t pt-4">
            <div className="flex items-center gap-4 text-xs mb-3">
              <span className="inline-flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded-sm bg-emerald-400"></span> Available
              </span>
              <span className="inline-flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded-sm bg-red-400"></span> Booked
              </span>
              <span className="text-gray-500 ml-auto">
                {seatmap.seats.filter(s => !s.booked).length} / {seatmap.total_seats} available
              </span>
            </div>
            <div
              className="grid gap-1.5 max-h-72 overflow-y-auto p-1"
              style={{ gridTemplateColumns: `repeat(${seatmap.columns}, minmax(0, 1fr))` }}
            >
              {seatmap.seats.map((s) => (
                <div
                  key={s.number}
                  title={s.number}
                  className={
                    "text-[10px] font-mono text-center rounded py-1 select-none " +
                    (s.booked
                      ? "bg-red-400 text-white"
                      : "bg-emerald-400 text-white")
                  }
                >
                  {s.number}
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      <Card className="p-6">
        <h2 className="font-semibold mb-3">Passengers</h2>
        <form onSubmit={submit} className="space-y-3">
          <ErrorBox message={err} />
          {passengers.map((p, i) => (
            <div key={i} className="grid grid-cols-12 gap-2 items-center">
              <input placeholder="Name" required value={p.name} onChange={(e) => update(i, "name", e.target.value)}
                     className="col-span-5 border border-gray-300 rounded-md px-3 py-2" />
              <input placeholder="Age" type="number" required min={1} max={120} value={p.age}
                     onChange={(e) => update(i, "age", e.target.value)}
                     className="col-span-3 border border-gray-300 rounded-md px-3 py-2" />
              <select value={p.gender} onChange={(e) => update(i, "gender", e.target.value)}
                      className="col-span-3 border border-gray-300 rounded-md px-3 py-2">
                <option value="MALE">Male</option>
                <option value="FEMALE">Female</option>
                <option value="OTHER">Other</option>
              </select>
              <button type="button" onClick={() => removePax(i)} disabled={passengers.length === 1}
                      className="col-span-1 text-red-600 text-sm disabled:opacity-40">x</button>
            </div>
          ))}
          {passengers.length < 6 && (
            <Button type="button" variant="neutral" onClick={addPax}>+ Add passenger</Button>
          )}
          <div className="border-t pt-4 flex items-center justify-between flex-wrap gap-3">
            <div className="text-sm text-gray-600">
              {selected ? <>Fare: Rs.{selected.fare} x {passengers.length} = <b>Rs.{selected.fare * passengers.length}</b></> : "Select a class"}
            </div>
            <Button type="submit" disabled={busy || !selected}>{busy ? "Booking..." : "Confirm Booking (Test Payment)"}</Button>
          </div>
        </form>
      </Card>
    </div>
  );
}