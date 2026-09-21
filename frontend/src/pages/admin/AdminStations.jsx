import { useEffect, useState } from "react";
import api from "../../services/api";
import { Button, Card, Empty, ErrorBox, Spinner } from "../../components/ui";

const blank = { name: "", code: "", city: "", state: "" };

export default function AdminStations() {
  const [stations, setStations] = useState(null);
  const [form, setForm] = useState(blank);
  const [editId, setEditId] = useState(null);
  const [err, setErr] = useState("");

  const load = () => api.get("/stations").then((r) => setStations(r.data.stations));
  useEffect(() => { load().catch((e) => setErr(e?.response?.data?.error || "Failed")); }, []);

  const submit = async (e) => {
    e.preventDefault(); setErr("");
    try {
      if (editId) await api.put(`/stations/${editId}`, form);
      else await api.post("/stations", form);
      setForm(blank); setEditId(null); load();
    } catch (ex) { setErr(ex?.response?.data?.error || "Save failed"); }
  };
  const del = async (id) => {
    if (!confirm("Delete this station?")) return;
    try { await api.delete(`/stations/${id}`); load(); }
    catch (ex) { setErr(ex?.response?.data?.error || "Delete failed"); }
  };
  const edit = (s) => { setEditId(s.id); setForm({ name: s.name, code: s.code, city: s.city, state: s.state }); };

  if (!stations) return <Spinner />;
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-navy-900">Stations</h1>
      <Card className="p-4">
        <form onSubmit={submit} className="grid md:grid-cols-5 gap-2 items-end">
          <ErrorBox message={err} />
          <input placeholder="Name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="border rounded px-2 py-1" />
          <input placeholder="Code" required value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="border rounded px-2 py-1" />
          <input placeholder="City" required value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} className="border rounded px-2 py-1" />
          <input placeholder="State" required value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} className="border rounded px-2 py-1" />
          <Button type="submit">{editId ? "Update" : "Add"}</Button>
        </form>
      </Card>
      <Card className="p-4">
        {stations.length === 0 ? <Empty message="No stations yet." /> : (
          <table className="w-full text-sm">
            <thead><tr className="text-left text-gray-500">
              <th className="py-2">Code</th><th>Name</th><th>City</th><th>State</th><th></th>
            </tr></thead>
            <tbody>
              {stations.map((s) => (
                <tr key={s.id} className="border-t">
                  <td className="py-2 font-mono">{s.code}</td>
                  <td>{s.name}</td><td>{s.city}</td><td>{s.state}</td>
                  <td className="space-x-2">
                    <button onClick={() => edit(s)} className="text-rail-600">Edit</button>
                    <button onClick={() => del(s.id)} className="text-red-600">Delete</button>
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
