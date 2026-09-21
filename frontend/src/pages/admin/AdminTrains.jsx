import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../services/api";
import { Button, Card, Empty, ErrorBox, Spinner } from "../../components/ui";

const blank = { train_number: "", train_name: "", train_type: "Express" };
const TYPES = ["Express", "Superfast", "Intercity", "Passenger", "Other"];

export default function AdminTrains() {
  const [trains, setTrains] = useState(null);
  const [form, setForm] = useState(blank);
  const [editId, setEditId] = useState(null);
  const [err, setErr] = useState("");

  const load = () => api.get("/trains").then((r) => setTrains(r.data.trains));
  useEffect(() => { load().catch((e) => setErr(e?.response?.data?.error || "Failed")); }, []);

  const submit = async (e) => {
    e.preventDefault(); setErr("");
    try {
      if (editId) await api.put(`/trains/${editId}`, form);
      else await api.post("/trains", form);
      setForm(blank); setEditId(null); load();
    } catch (ex) { setErr(ex?.response?.data?.error || "Save failed"); }
  };
  const toggle = async (t) => {
    try { await api.patch(`/trains/${t.id}/status`, { status: t.status === "ACTIVE" ? "INACTIVE" : "ACTIVE" }); load(); }
    catch (ex) { setErr(ex?.response?.data?.error || "Failed"); }
  };

  if (!trains) return <Spinner />;
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-navy-900">Trains</h1>
      <Card className="p-4">
        <form onSubmit={submit} className="grid md:grid-cols-4 gap-2 items-end">
          <ErrorBox message={err} />
          <input placeholder="Train number" required value={form.train_number}
                 onChange={(e) => setForm({ ...form, train_number: e.target.value })} className="border rounded px-2 py-1" />
          <input placeholder="Train name" required value={form.train_name}
                 onChange={(e) => setForm({ ...form, train_name: e.target.value })} className="border rounded px-2 py-1" />
          <select value={form.train_type} onChange={(e) => setForm({ ...form, train_type: e.target.value })} className="border rounded px-2 py-1">
            {TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
          <Button type="submit">{editId ? "Update" : "Add"}</Button>
        </form>
      </Card>
      <Card className="p-4">
        {trains.length === 0 ? <Empty message="No trains yet." /> : (
          <table className="w-full text-sm">
            <thead><tr className="text-left text-gray-500">
              <th className="py-2">Number</th><th>Name</th><th>Type</th><th>Status</th><th></th>
            </tr></thead>
            <tbody>
              {trains.map((t) => (
                <tr key={t.id} className="border-t">
                  <td className="py-2 font-mono">{t.train_number}</td>
                  <td>{t.train_name}</td><td>{t.train_type}</td>
                  <td><span className={`text-xs px-2 py-1 rounded ${t.status === "ACTIVE" ? "bg-green-100 text-green-800" : "bg-gray-200"}`}>{t.status}</span></td>
                  <td className="space-x-2">
                    <Link to={`/admin/trains/${t.id}`} className="text-rail-600">Manage</Link>
                    <button onClick={() => { setEditId(t.id); setForm({ train_number: t.train_number, train_name: t.train_name, train_type: t.train_type }); }}
                            className="text-rail-600">Edit</button>
                    <button onClick={() => toggle(t)} className="text-yellow-700">
                      {t.status === "ACTIVE" ? "Deactivate" : "Activate"}
                    </button>
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
