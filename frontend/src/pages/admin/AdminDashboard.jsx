import { useEffect, useState } from "react";
import api from "../../services/api";
import { Card, Empty, ErrorBox, Spinner } from "../../components/ui";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";

const COLORS = ["#2563eb", "#0f2a52", "#60a5fa", "#1e40af", "#93c5fd"];

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    Promise.all([api.get("/admin/dashboard"), api.get("/admin/analytics")])
      .then(([s, a]) => { setStats(s.data); setAnalytics(a.data); })
      .catch((e) => setErr(e?.response?.data?.error || "Failed to load dashboard"));
  }, []);

  if (err) return <ErrorBox message={err} />;
  if (!stats) return <Spinner />;

  const kpis = [
    ["Total Trains", stats.total_trains],
    ["Active Trains", stats.active_trains],
    ["Total Stations", stats.total_stations],
    ["Total Users", stats.total_users],
    ["Today's Bookings", stats.todays_bookings],
    ["Confirmed", stats.confirmed_bookings],
    ["Cancelled", stats.cancelled_bookings],
    ["Waitlisted", stats.waitlisted_bookings || 0],
    ["Revenue", `Rs.${stats.revenue}`],
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-navy-900">Admin Dashboard</h1>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {kpis.map(([label, v]) => (
          <Card key={label} className="p-4">
            <div className="text-xs text-gray-500">{label}</div>
            <div className="text-xl font-bold text-navy-900">{v}</div>
          </Card>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Card className="p-4">
          <h2 className="font-semibold mb-3">Bookings per day (30d)</h2>
          {analytics?.bookings_per_day?.length ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={analytics.bookings_per_day}>
                <XAxis dataKey="date" fontSize={11} />
                <YAxis fontSize={11} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          ) : <Empty message="No booking data available." />}
        </Card>

        <Card className="p-4">
          <h2 className="font-semibold mb-3">Bookings by class</h2>
          {analytics?.bookings_by_class?.length ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={analytics.bookings_by_class} dataKey="count" nameKey="class_name" outerRadius={90} label>
                  {analytics.bookings_by_class.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : <Empty message="No booking data available." />}
        </Card>

        <Card className="p-4">
          <h2 className="font-semibold mb-3">Popular trains</h2>
          {analytics?.popular_trains?.length ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={analytics.popular_trains} layout="vertical">
                <XAxis type="number" fontSize={11} allowDecimals={false} />
                <YAxis dataKey="train_number" type="category" fontSize={11} />
                <Tooltip />
                <Bar dataKey="count" fill="#0f2a52" />
              </BarChart>
            </ResponsiveContainer>
          ) : <Empty message="No booking data available." />}
        </Card>

        <Card className="p-4">
          <h2 className="font-semibold mb-3">Revenue by train</h2>
          {analytics?.revenue_by_train?.length ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={analytics.revenue_by_train}>
                <XAxis dataKey="train_number" fontSize={11} />
                <YAxis fontSize={11} />
                <Tooltip />
                <Bar dataKey="revenue" fill="#60a5fa" />
              </BarChart>
            </ResponsiveContainer>
          ) : <Empty message="No booking data available." />}
        </Card>
      </div>

      <Card className="p-4">
        <h2 className="font-semibold mb-3">Popular routes</h2>
        {analytics?.popular_routes?.length ? (
          <table className="w-full text-sm">
            <thead><tr className="text-left text-gray-500"><th className="py-1">From</th><th>To</th><th>Bookings</th></tr></thead>
            <tbody>
              {analytics.popular_routes.map((r, i) => (
                <tr key={i} className="border-t"><td className="py-1">{r.from}</td><td>{r.to}</td><td>{r.count}</td></tr>
              ))}
            </tbody>
          </table>
        ) : <Empty message="No booking data available." />}
      </Card>
    </div>
  );
}
