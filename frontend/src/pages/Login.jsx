import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Button, Card, ErrorBox } from "../components/ui";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      const u = await login(email.trim(), password);
      nav(u.role === "ADMIN" ? "/admin" : "/search");
    } catch (ex) {
      setErr(ex?.response?.data?.error || "Login failed");
    } finally { setBusy(false); }
  };

  return (
    <div className="max-w-md mx-auto mt-10">
      <Card className="p-6">
        <h1 className="text-2xl font-bold text-navy-900 mb-4">Login</h1>
        <form onSubmit={submit} className="space-y-4">
          <ErrorBox message={err} />
          <input type="email" placeholder="Email" value={email}
                 onChange={(e) => setEmail(e.target.value)} required
                 className="w-full border border-gray-300 rounded-md px-3 py-2" />
          <input type="password" placeholder="Password" value={password}
                 onChange={(e) => setPassword(e.target.value)} required
                 className="w-full border border-gray-300 rounded-md px-3 py-2" />
          <Button type="submit" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</Button>
        </form>
        <p className="text-sm text-gray-600 mt-4">
          No account? <Link to="/register" className="text-rail-600 hover:underline">Register</Link>
        </p>
      </Card>
    </div>
  );
}
