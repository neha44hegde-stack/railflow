import { useEffect, useState } from "react";
import api from "../../services/api";
import { Card, Empty, ErrorBox, Spinner } from "../../components/ui";

export default function AdminUsers() {
  const [users, setUsers] = useState(null);
  const [filters, setFilters] = useState({ q: "", role: "" });
  const [err, setErr] = useState("");

  const load = () => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => v && params.set(k, v));
    return api.get(`/admin/users?${params.toString()}`)
      .then((r) => setUsers(r.data.users))
      .catch((e) => setErr(e?.response?.data?.error || "Load failed"));
  };
  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-navy-900">Users</h1>
      <Card className="p-4 flex gap-2">
        <input placeholder="Search name or email" value={filters.q}
               onChange={(e) => setFilters({ ...filters, q: e.target.value })} className="border rounded px-2 py-1 flex-1" />
        <select value={filters.role} onChange={(e) => setFilters({ ...filters, role: e.target.value })} className="border rounded px-2 py-1">
          <option value="">Any role</option><option>PASSENGER</option><option>ADMIN</option>
        </select>
        <button onClick={load} className="bg-rail-600 text-white rounded px-3 py-1">Search</button>
      </Card>
      <ErrorBox message={err} />
      {!users ? <Spinner /> : users.length === 0 ? <Empty message="No users." /> : (
        <Card className="p-4">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-gray-500">
              <th className="py-2">Name</th><th>Email</th><th>Role</th><th>Bookings</th><th>Joined</th>
            </tr></thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t">
                  <td className="py-2">{u.name}</td><td>{u.email}</td>
                  <td>{u.role}</td><td>{u.booking_count}</td>
                  <td>{u.created_at?.slice(0, 10)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
