import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Button, Card, ErrorBox } from "../components/ui";

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "PASSENGER" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      const u = await register(form);
      nav(u.role === "ADMIN" ? "/admin" : "/search");
    } catch (ex) {
      setErr(ex?.response?.data?.error || "Registration failed");
    } finally { setBusy(false); }
  };

  return (
    <div className="max-w-md mx-auto mt-10">
      <Card className="p-6">
        <h1 className="text-2xl font-bold text-navy-900 mb-4">Create account</h1>
        <form onSubmit={submit} className="space-y-4">
          <ErrorBox message={err} />
          <input placeholder="Name" value={form.name} required
                 onChange={(e) => setForm({ ...form, name: e.target.value })}
                 className="w-full border border-gray-300 rounded-md px-3 py-2" />
          <input type="email" placeholder="Email" value={form.email} required
                 onChange={(e) => setForm({ ...form, email: e.target.value })}
                 className="w-full border border-gray-300 rounded-md px-3 py-2" />
          <input type="password" placeholder="Password (min 6)" value={form.password} required minLength={6}
                 onChange={(e) => setForm({ ...form, password: e.target.value })}
                 className="w-full border border-gray-300 rounded-md px-3 py-2" />
          <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2">
            <option value="PASSENGER">Passenger</option>
            <option value="ADMIN">Admin</option>
          </select>
          <Button type="submit" disabled={busy}>{busy ? "Creating…" : "Create account"}</Button>
        </form>
        <p className="text-sm text-gray-600 mt-4">
          Have an account? <Link to="/login" className="text-rail-600 hover:underline">Login</Link>
        </p>
      </Card>
    </div>
  );
}
