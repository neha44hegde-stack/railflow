"""Dev-only frontend served by Flask. Does not replace the React frontend."""
from flask import make_response
from config import Config
from app import create_app


class DevConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///railflow_dev.db"


HTML = r"""<!doctype html>
<html lang="en" class="light">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>RailFlow</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='20' fill='%230b1f3a'/%3E%3Cpath d='M30 70 L50 35 L70 70 M40 55 L60 55 M50 35 L50 70' stroke='%2360a5fa' stroke-width='6' fill='none' stroke-linecap='round'/%3E%3C/svg%3E" />
<script>
  (function() {
    var t = localStorage.getItem('rf_theme') || 'light';
    document.documentElement.classList.toggle('dark', t === 'dark');
    document.documentElement.classList.toggle('light', t === 'light');
  })();
</script>
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    darkMode: 'class',
    theme: {
      extend: {
        colors: {
          rail: {
            50:  '#eff6ff', 100: '#dbeafe', 200: '#bfdbfe',
            500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8',
            900: '#0b1f3a',
          },
        },
      },
    },
  };
</script>
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
<style>
  html, body { background: #f1f5f9; }
  html.dark, html.dark body { background: #0b1220; }
  ::-webkit-scrollbar { width: 10px; height: 10px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 6px; }
  html.dark ::-webkit-scrollbar-thumb { background: #334155; }
  .transition-theme, .transition-theme * {
    transition: background-color .18s ease, border-color .18s ease, color .18s ease;
  }
  @media print {
    header, .no-print { display: none !important; }
    body { background: white !important; }
  }
</style>
</head>
<body class="text-slate-800 dark:text-slate-100 transition-theme">
<div id="root"></div>
<script type="text/babel">
const { useState, useEffect } = React;

const API = "/api";
const token = () => localStorage.getItem("rf_token");
const setToken = t => t ? localStorage.setItem("rf_token", t) : localStorage.removeItem("rf_token");

async function call(method, path, body) {
  const r = await fetch(API + path, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token() ? { Authorization: "Bearer " + token() } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || ("HTTP " + r.status));
  return data;
}

function downloadCSV(filename, rows, columns) {
  if (!rows || rows.length === 0) { alert("Nothing to export."); return; }
  const esc = v => {
    const s = v === null || v === undefined ? "" : String(v);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  };
  const header = columns.map(c => esc(c.label)).join(",");
  const lines = rows.map(row => columns.map(c => esc(c.get(row))).join(","));
  const csv = "\uFEFF" + header + "\n" + lines.join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function ThemeToggle() {
  const [dark, setDark] = useState(document.documentElement.classList.contains("dark"));
  const toggle = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    document.documentElement.classList.toggle("light", !next);
    localStorage.setItem("rf_theme", next ? "dark" : "light");
  };
  return (
    <button onClick={toggle} title={dark ? "Light mode" : "Dark mode"}
      className="p-2 rounded-lg bg-slate-700/40 hover:bg-slate-600/60 text-slate-100 transition">
      {dark ? <SunIcon/> : <MoonIcon/>}
    </button>
  );
}

const Logo = ({ size = 32 }) => (
  <svg width={size} height={size} viewBox="0 0 100 100" className="shrink-0">
    <defs>
      <linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#3b82f6"/>
        <stop offset="100%" stopColor="#1d4ed8"/>
      </linearGradient>
    </defs>
    <rect width="100" height="100" rx="22" fill="url(#lg)"/>
    <path d="M28 72 L50 32 L72 72" stroke="#fff" strokeWidth="6" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M40 60 L60 60" stroke="#fff" strokeWidth="6" strokeLinecap="round"/>
    <circle cx="28" cy="72" r="6" fill="#fff"/>
    <circle cx="72" cy="72" r="6" fill="#fff"/>
  </svg>
);
const SunIcon = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>;
const MoonIcon = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>;
const DownloadIcon = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>;
const TrainIcon = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="3" width="16" height="16" rx="2"/><path d="M4 11h16M12 3v8M8 19l-2 3M16 19l2 3"/><circle cx="8.5" cy="15" r="1"/><circle cx="15.5" cy="15" r="1"/></svg>;
const TicketIcon = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3v1a2 2 0 0 0 0 4v1a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3v-1a2 2 0 0 0 0-4V9z"/><path d="M13 6v12"/></svg>;
const SearchIcon = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>;
const ShieldIcon = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>;

function Button({ children, onClick, variant = "primary", disabled, type = "button", className = "" }) {
  const v = {
    primary: "bg-blue-600 hover:bg-blue-500 text-white shadow-sm",
    danger:  "bg-red-600 hover:bg-red-500 text-white shadow-sm",
    neutral: "bg-slate-200 hover:bg-slate-300 text-slate-800 dark:bg-slate-700 dark:hover:bg-slate-600 dark:text-slate-100",
    ghost:   "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800",
  }[variant];
  return (
    <button type={type} onClick={onClick} disabled={disabled}
      className={"px-4 py-2 rounded-lg font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed transition " + v + " " + className}>
      {children}
    </button>
  );
}
const Card = ({ children, className = "" }) =>
  <div className={"bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm " + className}>{children}</div>;

const Input = (props) =>
  <input {...props} className={"w-full border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 " + (props.className || "")} />;

const Select = (props) =>
  <select {...props} className={"w-full border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 " + (props.className || "")} />;

const Badge = ({ status }) => {
  const s = status === "CONFIRMED" || status === "ACTIVE"
    ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300"
    : "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300";
  return <span className={"px-2.5 py-1 text-xs font-semibold rounded-full " + s}>{status}</span>;
};

const Spinner = ({ label = "Loading..." }) => (
  <div className="flex items-center gap-3 py-10 text-slate-500 dark:text-slate-400 text-sm justify-center">
    <span className="inline-block w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></span>
    {label}
  </div>
);

const Empty = ({ message, icon: Icon }) => (
  <div className="text-center py-14 text-slate-500 dark:text-slate-400">
    {Icon && <div className="flex justify-center mb-3 opacity-40"><Icon/></div>}
    <p className="text-sm">{message}</p>
  </div>
);

function Header({ user, setUser, setPage, currentPage }) {
  const logout = () => { setToken(null); setUser(null); setPage("home"); };
  const item = (label, key, icon) => {
    const active = currentPage === key;
    return (
      <button key={key} onClick={() => setPage(key)}
        className={"flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition " +
          (active ? "bg-blue-600 text-white" : "text-slate-200 hover:bg-slate-700/60")}>
        {icon}{label}
      </button>
    );
  };
  return (
    <header className="bg-slate-900 dark:bg-slate-950 border-b border-slate-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setPage("home")}>
          <Logo size={36}/>
          <div className="leading-tight">
            <div className="font-bold text-lg text-white tracking-wide">RAILFLOW</div>
            <div className="text-[10px] text-slate-400 uppercase tracking-widest">Railway Booking System</div>
          </div>
        </div>
        <nav className="flex items-center gap-1 flex-wrap">
          {!user && <>{item("Login", "login")}{item("Register", "register")}{item("PNR", "pnr")}</>}
          {user && user.role === "PASSENGER" && <>
            {item("Search", "search", <SearchIcon/>)}
            {item("My Bookings", "mybookings", <TicketIcon/>)}
            {item("PNR", "pnr", <TicketIcon/>)}
          </>}
          {user && user.role === "ADMIN" && <>
            {item("Dashboard", "dashboard")}
            {item("Stations", "stations")}
            {item("Trains", "trains", <TrainIcon/>)}
            {item("Bookings", "bookings")}
            {item("Users", "users")}
          </>}
          <ThemeToggle/>
          {user && (
            <div className="flex items-center gap-2 ml-2 pl-2 border-l border-slate-700">
              <div className="w-8 h-8 rounded-full bg-blue-600 text-white grid place-items-center text-xs font-bold">
                {user.name.slice(0,1).toUpperCase()}
              </div>
              <div className="leading-tight hidden sm:block">
                <div className="text-xs font-semibold text-white">{user.name}</div>
                <div className="text-[10px] text-slate-400 uppercase">{user.role}</div>
              </div>
              <button onClick={logout} className="ml-1 text-xs text-slate-300 hover:text-white underline">Logout</button>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}

function Home({ setPage }) {
  return (
    <div className="py-16 text-center">
      <div className="inline-flex items-center justify-center w-20 h-20 mb-6"><Logo size={80}/></div>
      <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 dark:text-white tracking-tight">RailFlow</h1>
      <p className="text-slate-600 dark:text-slate-400 mt-3 max-w-md mx-auto">
        A modern railway reservation system - search, book, and manage your journey.
      </p>
      <div className="mt-8 flex justify-center gap-3 flex-wrap">
        <Button onClick={() => setPage("search")}><span className="inline-flex items-center gap-2"><SearchIcon/>Search Trains</span></Button>
        <Button variant="neutral" onClick={() => setPage("pnr")}>Check PNR</Button>
      </div>
      <div className="mt-16 grid sm:grid-cols-3 gap-4 max-w-3xl mx-auto text-left">
        {[
          { icon: SearchIcon, title: "Search & Book", text: "Find trains by route and date." },
          { icon: TicketIcon, title: "Instant PNR", text: "Real PNR generated for every ticket." },
          { icon: ShieldIcon, title: "Secure", text: "JWT auth, hashed passwords, role-based access." },
        ].map(({icon: Icon, title, text}) => (
          <Card key={title} className="p-5">
            <div className="text-blue-600 dark:text-blue-400 mb-2"><Icon/></div>
            <h3 className="font-semibold text-slate-900 dark:text-white">{title}</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{text}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}

function Auth({ mode, setUser, setPage }) {
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "PASSENGER" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async e => {
    e.preventDefault(); setErr(""); setBusy(true);
    try {
      if (mode === "register") await call("POST", "/auth/register", form);
      const r = await call("POST", "/auth/login", { email: form.email, password: form.password });
      setToken(r.access_token); setUser(r.user);
      setPage(r.user.role === "ADMIN" ? "dashboard" : "search");
    } catch (ex) { setErr(ex.message); } finally { setBusy(false); }
  };
  return (
    <div className="max-w-md mx-auto mt-12">
      <Card className="p-8">
        <div className="flex items-center gap-3 mb-6">
          <Logo size={40}/>
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">{mode === "register" ? "Create account" : "Welcome back"}</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">{mode === "register" ? "Sign up for RailFlow" : "Sign in to continue"}</p>
          </div>
        </div>
        {err && <div className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 p-3 rounded-lg mb-4 text-sm border border-red-200 dark:border-red-800">{err}</div>}
        <form onSubmit={submit} className="space-y-3">
          {mode === "register" && (
            <Input placeholder="Full name" required value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })} />
          )}
          <Input type="email" placeholder="Email address" required value={form.email}
            onChange={e => setForm({ ...form, email: e.target.value })} />
          <Input type="password" placeholder="Password" required value={form.password}
            onChange={e => setForm({ ...form, password: e.target.value })} />
          {mode === "register" && (
            <Select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
              <option value="PASSENGER">Passenger</option>
              <option value="ADMIN">Administrator</option>
            </Select>
          )}
          <Button type="submit" disabled={busy} className="w-full">
            {busy ? "Please wait..." : (mode === "register" ? "Create account" : "Sign in")}
          </Button>
        </form>
        <p className="text-sm mt-5 text-slate-600 dark:text-slate-400 text-center">
          {mode === "register" ? "Already have an account? " : "New to RailFlow? "}
          <button className="text-blue-600 dark:text-blue-400 underline font-medium"
            onClick={() => setPage(mode === "register" ? "login" : "register")}>
            {mode === "register" ? "Sign in" : "Create one"}
          </button>
        </p>
      </Card>
    </div>
  );
}

function Search({ setPage }) {
  const [stations, setStations] = useState([]);
  const [form, setForm] = useState({
    source: "", destination: "",
    date: new Date(Date.now() + 86400000).toISOString().slice(0, 10),
    class: "",
  });
  const [results, setResults] = useState(null);
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  useEffect(() => { call("GET", "/stations").then(r => setStations(r.stations)).catch(e => setErr(e.message)); }, []);
  const search = async e => {
    e.preventDefault(); setErr(""); setBusy(true); setResults(null);
    try {
      const p = new URLSearchParams({ source: form.source, destination: form.destination, date: form.date });
      if (form.class) p.set("class", form.class);
      const r = await call("GET", "/trains/search?" + p);
      setResults(r.trains);
    } catch (ex) { setErr(ex.message); } finally { setBusy(false); }
  };
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Search Trains</h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Find the perfect journey for your schedule.</p>
      </div>
      <Card className="p-6">
        <form onSubmit={search} className="grid md:grid-cols-5 gap-3">
          <Select required value={form.source} onChange={e => setForm({...form, source: e.target.value})}>
            <option value="">From station</option>
            {stations.map(s => <option key={s.id} value={s.id}>{s.name} ({s.code})</option>)}
          </Select>
          <Select required value={form.destination} onChange={e => setForm({...form, destination: e.target.value})}>
            <option value="">To station</option>
            {stations.map(s => <option key={s.id} value={s.id}>{s.name} ({s.code})</option>)}
          </Select>
          <Input type="date" value={form.date} onChange={e => setForm({...form, date: e.target.value})} />
          <Select value={form.class} onChange={e => setForm({...form, class: e.target.value})}>
            <option value="">Any class</option>
            {["Sleeper","AC 3 Tier","AC 2 Tier","AC 1 Tier","Chair Car"].map(c => <option key={c}>{c}</option>)}
          </Select>
          <Button type="submit" disabled={busy}>{busy ? "Searching..." : "Search"}</Button>
        </form>
      </Card>
      {err && <div className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 p-3 rounded-lg text-sm">{err}</div>}
      {busy && <Spinner label="Searching trains..."/>}
      {results && results.length === 0 && <Empty message="No trains found for this route and date." icon={TrainIcon}/>}
      {results && results.map(r => (
        <Card key={r.train.id} className="p-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 grid place-items-center">
                <TrainIcon/>
              </div>
              <div>
                <div className="font-bold text-slate-900 dark:text-white">
                  <span className="font-mono">{r.train.train_number}</span> - {r.train.train_name}
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-400 mt-0.5">
                  {r.source.station.name} <span className="text-slate-400">({r.departure||"--"})</span>
                  <span className="mx-2 text-slate-400">to</span>
                  {r.destination.station.name} <span className="text-slate-400">({r.arrival||"--"})</span>
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-500 mt-1">{r.train.train_type}</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {r.classes.map(c => (
                <div key={c.class_name} className="border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-2 text-sm min-w-[110px]">
                  <div className="font-medium text-slate-900 dark:text-white">{c.class_name}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    <span className="font-semibold text-slate-700 dark:text-slate-300">Rs.{c.fare}</span>
                    <span className="mx-1">|</span>
                    <span className={c.available_seats > 0 ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"}>
                      {c.available_seats} left
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <Button onClick={() => setPage({ name: "book", trainId: r.train.id, source: r.source.station.id, destination: r.destination.station.id, date: form.date })}>Book</Button>
          </div>
        </Card>
      ))}
    </div>
  );
}

function Book({ ctx, setPage }) {
  const [train, setTrain] = useState(null);
  const [classes, setClasses] = useState([]);
  const [cls, setCls] = useState("");
  const [pax, setPax] = useState([{ name: "", age: "", gender: "MALE" }]);
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  useEffect(() => {
    Promise.all([call("GET", "/trains/" + ctx.trainId), call("GET", "/trains/" + ctx.trainId + "/classes")])
      .then(([t, c]) => { setTrain(t.train); setClasses(c.classes); if (c.classes[0]) setCls(c.classes[0].class_name); })
      .catch(e => setErr(e.message));
  }, [ctx.trainId]);
  const update = (i, k, v) => { const c = [...pax]; c[i][k] = v; setPax(c); };
  const submit = async e => {
    e.preventDefault(); setErr(""); setBusy(true);
    try {
      const r = await call("POST", "/bookings", {
        train_id: parseInt(ctx.trainId, 10), journey_date: ctx.date,
        source_station_id: parseInt(ctx.source, 10), destination_station_id: parseInt(ctx.destination, 10),
        class_name: cls, passengers: pax.map(p => ({ ...p, age: parseInt(p.age, 10) })),
      });
      setPage({ name: "ticket", pnr: r.booking.pnr });
    } catch (ex) { setErr(ex.message); } finally { setBusy(false); }
  };
  if (!train) return <Spinner/>;
  const sel = classes.find(c => c.class_name === cls);
  return (
    <div className="space-y-5 max-w-4xl mx-auto">
      <Card className="p-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 grid place-items-center"><TrainIcon/></div>
          <div>
            <div className="font-bold text-lg text-slate-900 dark:text-white">
              <span className="font-mono">{train.train_number}</span> - {train.train_name}
            </div>
            <div className="text-sm text-slate-500 dark:text-slate-400">Journey date: {ctx.date}</div>
          </div>
        </div>
      </Card>
      <Card className="p-6">
        <h3 className="font-semibold text-slate-900 dark:text-white mb-3">Select class</h3>
        <div className="grid sm:grid-cols-3 gap-3">
          {classes.map(c => (
            <label key={c.class_name}
              className={"border rounded-lg p-4 cursor-pointer transition " +
                (cls === c.class_name
                  ? "border-blue-600 bg-blue-50 dark:bg-blue-900/30 dark:border-blue-500 ring-2 ring-blue-500/20"
                  : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600")}>
              <input type="radio" className="hidden" checked={cls === c.class_name} onChange={() => setCls(c.class_name)}/>
              <div className="font-medium text-slate-900 dark:text-white">{c.class_name}</div>
              <div className="text-sm text-slate-600 dark:text-slate-400 mt-1">Rs.{c.fare}</div>
            </label>
          ))}
        </div>
      </Card>
      <Card className="p-6">
        <h3 className="font-semibold text-slate-900 dark:text-white mb-3">Passenger details</h3>
        <form onSubmit={submit} className="space-y-3">
          {err && <div className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 p-3 rounded-lg text-sm">{err}</div>}
          {pax.map((p, i) => (
            <div key={i} className="grid grid-cols-12 gap-2 items-center">
              <Input placeholder="Passenger name" required value={p.name} onChange={e => update(i, "name", e.target.value)} className="col-span-5"/>
              <Input type="number" placeholder="Age" required min={1} max={120} value={p.age} onChange={e => update(i, "age", e.target.value)} className="col-span-3"/>
              <Select value={p.gender} onChange={e => update(i, "gender", e.target.value)} className="col-span-3">
                <option value="MALE">Male</option><option value="FEMALE">Female</option><option value="OTHER">Other</option>
              </Select>
              <button type="button" disabled={pax.length === 1} onClick={() => setPax(pax.filter((_, idx) => idx !== i))}
                className="col-span-1 text-red-600 dark:text-red-400 disabled:opacity-30 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg py-2 transition">x</button>
            </div>
          ))}
          {pax.length < 6 && (
            <Button variant="ghost" onClick={() => setPax([...pax, { name: "", age: "", gender: "MALE" }])}>+ Add passenger</Button>
          )}
          <div className="border-t border-slate-200 dark:border-slate-800 pt-4 flex justify-between items-center flex-wrap gap-3">
            <div className="text-sm text-slate-600 dark:text-slate-400">
              {sel ? <>Fare: Rs.{sel.fare} x {pax.length} = <span className="font-bold text-slate-900 dark:text-white">Rs.{sel.fare * pax.length}</span></> : "Select a class to continue"}
            </div>
            <Button type="submit" disabled={busy || !sel}>{busy ? "Processing..." : "Confirm Booking (Test Payment)"}</Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

function MyBookings({ setPage }) {
  const [items, setItems] = useState(null); const [err, setErr] = useState("");
  const load = () => call("GET", "/bookings/my").then(r => setItems(r.bookings)).catch(e => setErr(e.message));
  useEffect(load, []);
  const cancel = async id => {
    if (!confirm("Cancel this booking?")) return;
    try { await call("POST", "/bookings/" + id + "/cancel"); load(); } catch (ex) { alert(ex.message); }
  };
  const exportCSV = () => downloadCSV("my-bookings.csv", items || [], [
    { label: "PNR", get: b => b.pnr },
    { label: "Train Number", get: b => b.train?.train_number || "" },
    { label: "Train Name", get: b => b.train?.train_name || "" },
    { label: "Journey Date", get: b => b.journey_date },
    { label: "From", get: b => b.source_station?.name || "" },
    { label: "To", get: b => b.destination_station?.name || "" },
    { label: "Class", get: b => b.class_name },
    { label: "Amount", get: b => b.total_amount },
    { label: "Status", get: b => b.status },
  ]);
  if (!items) return <Spinner/>;
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">My Bookings</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{items.length} booking(s) total</p>
        </div>
        <Button variant="neutral" onClick={exportCSV} className="inline-flex items-center gap-2"><DownloadIcon/>Export CSV</Button>
      </div>
      {err && <div className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 p-3 rounded-lg text-sm">{err}</div>}
      {items.length === 0 && <Card><Empty message="No bookings yet. Search for a train to get started." icon={TicketIcon}/></Card>}
      {items.map(b => (
        <Card key={b.id} className="p-5">
          <div className="flex justify-between flex-wrap gap-4">
            <div>
              <div className="font-mono font-bold text-blue-600 dark:text-blue-400">{b.pnr}</div>
              <div className="text-sm text-slate-700 dark:text-slate-300 mt-1">
                <span className="font-mono">{b.train?.train_number}</span> - {b.train?.train_name}
              </div>
              <div className="text-sm text-slate-600 dark:text-slate-400">
                {b.source_station?.name} to {b.destination_station?.name}
              </div>
              <div className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                {b.journey_date} | {b.class_name} | <span className="font-semibold">Rs.{b.total_amount}</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge status={b.status}/>
              <button onClick={() => setPage({ name: "ticket", pnr: b.pnr })}
                className="text-blue-600 dark:text-blue-400 text-sm font-medium hover:underline">View Ticket</button>
              {b.status === "CONFIRMED" && <Button variant="danger" onClick={() => cancel(b.id)}>Cancel</Button>}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

function Pnr() {
  const [pnr, setPnr] = useState(""); const [b, setB] = useState(null); const [err, setErr] = useState("");
  const lookup = async e => {
    e.preventDefault(); setErr(""); setB(null);
    try { const r = await call("GET", "/pnr/" + pnr.trim()); setB(r.booking); } catch (ex) { setErr(ex.message); }
  };
  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <Card className="p-6">
        <h2 className="font-bold text-lg text-slate-900 dark:text-white mb-1">PNR Status</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">Enter your 12-character PNR to view booking status.</p>
        <form onSubmit={lookup} className="flex gap-2">
          <Input placeholder="e.g. RF2026123456" required value={pnr} onChange={e => setPnr(e.target.value)} />
          <Button type="submit">Check</Button>
        </form>
        {err && <div className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 p-3 rounded-lg mt-3 text-sm">{err}</div>}
      </Card>
      {b && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="font-mono font-bold text-lg text-blue-600 dark:text-blue-400">{b.pnr}</div>
            <Badge status={b.status}/>
          </div>
          <div className="grid sm:grid-cols-2 gap-3 text-sm">
            <InfoRow l="Train" v={(b.train?.train_number||"") + " - " + (b.train?.train_name||"")}/>
            <InfoRow l="Journey Date" v={b.journey_date}/>
            <InfoRow l="From" v={b.source_station?.name}/>
            <InfoRow l="To" v={b.destination_station?.name}/>
            <InfoRow l="Class" v={b.class_name}/>
            <InfoRow l="Amount" v={"Rs." + b.total_amount}/>
          </div>
        </Card>
      )}
    </div>
  );
}

const InfoRow = ({ l, v }) => (
  <div className="flex justify-between border-b border-slate-100 dark:border-slate-800 py-2">
    <span className="text-slate-500 dark:text-slate-400">{l}</span>
    <span className="font-medium text-slate-900 dark:text-white">{v}</span>
  </div>
);

function Ticket({ ctx }) {
  const [b, setB] = useState(null); const [err, setErr] = useState("");
  useEffect(() => { call("GET", "/pnr/" + ctx.pnr).then(r => setB(r.booking)).catch(e => setErr(e.message)); }, [ctx.pnr]);
  if (err) return <Card className="p-6 text-red-700 dark:text-red-400">{err}</Card>;
  if (!b) return <Spinner/>;
  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div className="flex justify-end gap-2 no-print">
        <Button variant="neutral" onClick={() => window.print()} className="inline-flex items-center gap-2">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2M6 14h12v8H6z"/></svg>
          Print Ticket
        </Button>
      </div>
      <Card className="overflow-hidden">
        <div className="bg-slate-900 text-white p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Logo size={48}/>
            <div>
              <div className="font-bold text-xl tracking-wide">RAILFLOW</div>
              <div className="text-xs text-slate-400 uppercase tracking-widest">Electronic Ticket</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-slate-400 uppercase">PNR</div>
            <div className="font-mono font-bold text-lg">{b.pnr}</div>
          </div>
        </div>
        <div className="p-6 grid md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 font-semibold mb-3">Journey</h3>
            <div className="space-y-1 text-sm">
              <InfoRow l="Train" v={(b.train?.train_number||"") + " - " + (b.train?.train_name||"")}/>
              <InfoRow l="Date" v={b.journey_date}/>
              <InfoRow l="From" v={b.source_station?.name}/>
              <InfoRow l="To" v={b.destination_station?.name}/>
              <InfoRow l="Class" v={b.class_name}/>
              <InfoRow l="Total Fare" v={"Rs." + b.total_amount}/>
              <InfoRow l="Status" v={b.status}/>
            </div>
          </div>
          <div>
            <h3 className="text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 font-semibold mb-3">Passengers</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                  <th className="py-2 font-medium">Name</th><th className="font-medium">Age</th><th className="font-medium">Seat</th>
                </tr>
              </thead>
              <tbody>
                {b.passengers.map(p => (
                  <tr key={p.id} className="border-b border-slate-100 dark:border-slate-800">
                    <td className="py-2 text-slate-900 dark:text-white">{p.name}</td>
                    <td className="text-slate-700 dark:text-slate-300">{p.age} / {p.gender.slice(0,1)}</td>
                    <td className="font-mono font-semibold text-blue-600 dark:text-blue-400">{p.seat_number}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="bg-slate-50 dark:bg-slate-950 px-6 py-3 text-xs text-slate-500 dark:text-slate-400 border-t border-slate-200 dark:border-slate-800">
          This is a demo E-Ticket generated by RailFlow. Not a valid Indian Railways ticket.
        </div>
      </Card>
    </div>
  );
}

function AdminDashboard() {
  const [s, setS] = useState(null); const [err, setErr] = useState("");
  useEffect(() => { call("GET", "/admin/dashboard").then(setS).catch(e => setErr(e.message)); }, []);
  if (!s) return <Spinner/>;
  const kpis = [
    { label: "Total Trains", value: s.total_trains, color: "blue" },
    { label: "Active Trains", value: s.active_trains, color: "emerald" },
    { label: "Stations", value: s.total_stations, color: "violet" },
    { label: "Users", value: s.total_users, color: "amber" },
    { label: "Today's Bookings", value: s.todays_bookings, color: "cyan" },
    { label: "Confirmed", value: s.confirmed_bookings, color: "emerald" },
    { label: "Cancelled", value: s.cancelled_bookings, color: "red" },
    { label: "Revenue", value: "Rs." + s.revenue, color: "blue" },
  ];
  const bg = { blue: "bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400",
               emerald: "bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400",
               violet: "bg-violet-50 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400",
               amber: "bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400",
               cyan: "bg-cyan-50 dark:bg-cyan-900/30 text-cyan-600 dark:text-cyan-400",
               red: "bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400" };
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Admin Dashboard</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Overview of RailFlow operations.</p>
      </div>
      {err && <div className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 p-3 rounded-lg text-sm">{err}</div>}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {kpis.map(k => (
          <Card key={k.label} className="p-5">
            <div className={"w-10 h-10 rounded-lg grid place-items-center mb-3 " + bg[k.color]}><TrainIcon/></div>
            <div className="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold">{k.label}</div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{k.value}</div>
          </Card>
        ))}
      </div>
    </div>
  );
}

function AdminStations() {
  const [items, setItems] = useState(null); const [form, setForm] = useState({name:"",code:"",city:"",state:""}); const [err, setErr] = useState("");
  const load = () => call("GET", "/stations").then(r => setItems(r.stations)).catch(e => setErr(e.message));
  useEffect(load, []);
  const submit = async e => {
    e.preventDefault(); setErr("");
    try { await call("POST", "/stations", form); setForm({name:"",code:"",city:"",state:""}); load(); } catch (ex) { setErr(ex.message); }
  };
  const del = async id => { if (!confirm("Delete?")) return; try { await call("DELETE", "/stations/" + id); load(); } catch (ex) { setErr(ex.message); } };
  const exportCSV = () => downloadCSV("stations.csv", items || [], [
    { label: "Code", get: s => s.code }, { label: "Name", get: s => s.name },
    { label: "City", get: s => s.city }, { label: "State", get: s => s.state },
  ]);
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Stations</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Manage railway stations in the network.</p>
        </div>
        <Button variant="neutral" onClick={exportCSV} className="inline-flex items-center gap-2"><DownloadIcon/>Export CSV</Button>
      </div>
      <Card className="p-5">
        <form onSubmit={submit} className="grid md:grid-cols-5 gap-3">
          <Input placeholder="Station name" required value={form.name} onChange={e => setForm({...form, name: e.target.value})}/>
          <Input placeholder="Code (BNC)" required value={form.code} onChange={e => setForm({...form, code: e.target.value})}/>
          <Input placeholder="City" required value={form.city} onChange={e => setForm({...form, city: e.target.value})}/>
          <Input placeholder="State" required value={form.state} onChange={e => setForm({...form, state: e.target.value})}/>
          <Button type="submit">Add Station</Button>
        </form>
      </Card>
      {err && <div className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 p-3 rounded-lg text-sm">{err}</div>}
      {items && items.length === 0 && <Card><Empty message="No stations yet." icon={TrainIcon}/></Card>}
      {items && items.length > 0 && (
        <Card className="overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-950 text-slate-500 dark:text-slate-400 text-xs uppercase tracking-wider">
              <tr><th className="text-left py-3 px-4 font-medium">Code</th><th className="text-left font-medium">Name</th><th className="text-left font-medium">City</th><th className="text-left font-medium">State</th><th className="font-medium"></th></tr>
            </thead>
            <tbody>
              {items.map(s => (
                <tr key={s.id} className="border-t border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40">
                  <td className="py-3 px-4 font-mono font-semibold text-blue-600 dark:text-blue-400">{s.code}</td>
                  <td className="text-slate-900 dark:text-white">{s.name}</td>
                  <td className="text-slate-600 dark:text-slate-400">{s.city}</td>
                  <td className="text-slate-600 dark:text-slate-400">{s.state}</td>
                  <td className="text-right pr-4"><button onClick={() => del(s.id)} className="text-red-600 dark:text-red-400 text-sm hover:underline">Delete</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

function AdminTrains() {
  const [items, setItems] = useState(null); const [form, setForm] = useState({train_number:"",train_name:"",train_type:"Express"}); const [err, setErr] = useState("");
  const load = () => call("GET", "/trains").then(r => setItems(r.trains)).catch(e => setErr(e.message));
  useEffect(load, []);
  const submit = async e => { e.preventDefault(); setErr(""); try { await call("POST", "/trains", form); setForm({train_number:"",train_name:"",train_type:"Express"}); load(); } catch (ex) { setErr(ex.message); } };
  const toggle = async t => { try { await call("PATCH", "/trains/" + t.id + "/status", { status: t.status === "ACTIVE" ? "INACTIVE" : "ACTIVE" }); load(); } catch (ex) { setErr(ex.message); } };
  const exportCSV = () => downloadCSV("trains.csv", items || [], [
    { label: "Number", get: t => t.train_number }, { label: "Name", get: t => t.train_name },
    { label: "Type", get: t => t.train_type }, { label: "Status", get: t => t.status },
  ]);
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Trains</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Manage train fleet and their status.</p>
        </div>
        <Button variant="neutral" onClick={exportCSV} className="inline-flex items-center gap-2"><DownloadIcon/>Export CSV</Button>
      </div>
      <Card className="p-5">
        <form onSubmit={submit} className="grid md:grid-cols-4 gap-3">
          <Input placeholder="Train number" required value={form.train_number} onChange={e => setForm({...form, train_number: e.target.value})}/>
          <Input placeholder="Train name" required value={form.train_name} onChange={e => setForm({...form, train_name: e.target.value})}/>
          <Select value={form.train_type} onChange={e => setForm({...form, train_type: e.target.value})}>
            {["Express","Superfast","Intercity","Passenger","Other"].map(t => <option key={t}>{t}</option>)}
          </Select>
          <Button type="submit">Add Train</Button>
        </form>
      </Card>
      {err && <div className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 p-3 rounded-lg text-sm">{err}</div>}
      {items && items.length === 0 && <Card><Empty message="No trains yet." icon={TrainIcon}/></Card>}
      {items && items.length > 0 && (
        <Card className="overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-950 text-slate-500 dark:text-slate-400 text-xs uppercase tracking-wider">
              <tr><th className="text-left py-3 px-4 font-medium">Number</th><th className="text-left font-medium">Name</th><th className="text-left font-medium">Type</th><th className="text-left font-medium">Status</th><th className="font-medium"></th></tr>
            </thead>
            <tbody>
              {items.map(t => (
                <tr key={t.id} className="border-t border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40">
                  <td className="py-3 px-4 font-mono font-semibold text-blue-600 dark:text-blue-400">{t.train_number}</td>
                  <td className="text-slate-900 dark:text-white">{t.train_name}</td>
                  <td className="text-slate-600 dark:text-slate-400">{t.train_type}</td>
                  <td><Badge status={t.status}/></td>
                  <td className="text-right pr-4"><button onClick={() => toggle(t)} className="text-amber-600 dark:text-amber-400 text-sm hover:underline">{t.status === "ACTIVE" ? "Deactivate" : "Activate"}</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

function AdminBookings() {
  const [items, setItems] = useState(null); const [err, setErr] = useState("");
  useEffect(() => { call("GET", "/admin/bookings").then(r => setItems(r.bookings)).catch(e => setErr(e.message)); }, []);
  const exportCSV = () => downloadCSV("all-bookings.csv", items || [], [
    { label: "PNR", get: b => b.pnr },
    { label: "Train", get: b => (b.train?.train_number || "") + " " + (b.train?.train_name || "") },
    { label: "Journey Date", get: b => b.journey_date },
    { label: "From", get: b => b.source_station?.name || "" },
    { label: "To", get: b => b.destination_station?.name || "" },
    { label: "Class", get: b => b.class_name },
    { label: "Amount", get: b => b.total_amount },
    { label: "Status", get: b => b.status },
  ]);
  if (!items) return <Spinner/>;
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">All Bookings</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{items.length} booking(s) recorded.</p>
        </div>
        <Button variant="neutral" onClick={exportCSV} className="inline-flex items-center gap-2"><DownloadIcon/>Export CSV</Button>
      </div>
      {err && <div className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 p-3 rounded-lg text-sm">{err}</div>}
      {items.length === 0 ? <Card><Empty message="No bookings yet." icon={TicketIcon}/></Card> : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 dark:bg-slate-950 text-slate-500 dark:text-slate-400 text-xs uppercase tracking-wider">
                <tr>
                  <th className="text-left py-3 px-4 font-medium">PNR</th>
                  <th className="text-left font-medium">Train</th>
                  <th className="text-left font-medium">Journey</th>
                  <th className="text-left font-medium">Route</th>
                  <th className="text-left font-medium">Class</th>
                  <th className="text-left font-medium">Amount</th>
                  <th className="text-left font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {items.map(b => (
                  <tr key={b.id} className="border-t border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="py-3 px-4 font-mono font-semibold text-blue-600 dark:text-blue-400">{b.pnr}</td>
                    <td className="text-slate-900 dark:text-white">{b.train?.train_number}</td>
                    <td className="text-slate-600 dark:text-slate-400">{b.journey_date}</td>
                    <td className="text-slate-600 dark:text-slate-400">{(b.source_station?.name||"") + " to " + (b.destination_station?.name||"")}</td>
                    <td className="text-slate-600 dark:text-slate-400">{b.class_name}</td>
                    <td className="text-slate-900 dark:text-white font-semibold">Rs.{b.total_amount}</td>
                    <td><Badge status={b.status}/></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}

function AdminUsers() {
  const [items, setItems] = useState(null); const [err, setErr] = useState("");
  useEffect(() => { call("GET", "/admin/users").then(r => setItems(r.users)).catch(e => setErr(e.message)); }, []);
  const exportCSV = () => downloadCSV("users.csv", items || [], [
    { label: "Name", get: u => u.name }, { label: "Email", get: u => u.email },
    { label: "Role", get: u => u.role }, { label: "Bookings", get: u => u.booking_count },
    { label: "Joined", get: u => u.created_at || "" },
  ]);
  if (!items) return <Spinner/>;
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Users</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{items.length} user(s) registered.</p>
        </div>
        <Button variant="neutral" onClick={exportCSV} className="inline-flex items-center gap-2"><DownloadIcon/>Export CSV</Button>
      </div>
      {err && <div className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 p-3 rounded-lg text-sm">{err}</div>}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-950 text-slate-500 dark:text-slate-400 text-xs uppercase tracking-wider">
              <tr>
                <th className="text-left py-3 px-4 font-medium">Name</th>
                <th className="text-left font-medium">Email</th>
                <th className="text-left font-medium">Role</th>
                <th className="text-left font-medium">Bookings</th>
              </tr>
            </thead>
            <tbody>
              {items.map(u => (
                <tr key={u.id} className="border-t border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40">
                  <td className="py-3 px-4 text-slate-900 dark:text-white font-medium">{u.name}</td>
                  <td className="text-slate-600 dark:text-slate-400">{u.email}</td>
                  <td><span className={"px-2.5 py-1 text-xs font-semibold rounded-full " + (u.role === "ADMIN" ? "bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-300" : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300")}>{u.role}</span></td>
                  <td className="text-slate-600 dark:text-slate-400">{u.booking_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [page, setPage] = useState("home");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (token()) call("GET", "/auth/me").then(r => setUser(r.user)).catch(() => setToken(null)).finally(() => setLoading(false));
    else setLoading(false);
  }, []);
  if (loading) return <Spinner label="Starting RailFlow..."/>;
  const p = typeof page === "string" ? { name: page } : page;
  return (
    <>
      <Header user={user} setUser={setUser} setPage={setPage} currentPage={p.name}/>
      <main className="max-w-7xl mx-auto px-4 py-8">
        {p.name === "home" && <Home setPage={setPage}/>}
        {p.name === "login" && <Auth mode="login" setUser={setUser} setPage={setPage}/>}
        {p.name === "register" && <Auth mode="register" setUser={setUser} setPage={setPage}/>}
        {p.name === "search" && <Search setPage={setPage}/>}
        {p.name === "book" && <Book ctx={p} setPage={setPage}/>}
        {p.name === "mybookings" && <MyBookings setPage={setPage}/>}
        {p.name === "pnr" && <Pnr/>}
        {p.name === "ticket" && <Ticket ctx={p}/>}
        {p.name === "dashboard" && <AdminDashboard/>}
        {p.name === "stations" && <AdminStations/>}
        {p.name === "trains" && <AdminTrains/>}
        {p.name === "bookings" && <AdminBookings/>}
        {p.name === "users" && <AdminUsers/>}
      </main>
      <footer className="max-w-7xl mx-auto px-4 py-6 text-xs text-slate-400 dark:text-slate-600 text-center no-print">
        RailFlow | Demo system | Not affiliated with Indian Railways
      </footer>
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
</script>
</body>
</html>"""


app = create_app(DevConfig)


@app.route("/")
def _dev_index():
    resp = make_response(HTML)
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp


if __name__ == "__main__":
    app.run(debug=True, port=5000)