import { useEffect, useState } from "react";
import api from "../../services/api";
import { Card, Empty, ErrorBox, Spinner } from "../../components/ui";

export default function AdminAuditLog() {
  const [logs, setLogs] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get("/admin/audit")
      .then((r) => setLogs(r.data.logs))
      .catch((e) => setErr(e?.response?.data?.error || "Failed to load audit log"));
  }, []);

  if (err) return <ErrorBox message={err} />;
  if (!logs) return <Spinner />;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-navy-900">Audit Log</h1>
      <p className="text-sm text-gray-600">
        Every admin action is recorded here — {logs.length} entries.
      </p>
      {logs.length === 0 ? <Empty message="No audit entries yet." /> : (
        <Card className="p-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500">
                <th className="py-2">When</th>
                <th>Admin</th>
                <th>Action</th>
                <th>Entity</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id} className="border-t">
                  <td className="py-2 text-gray-600 whitespace-nowrap">
                    {l.created_at ? l.created_at.slice(0, 19).replace("T", " ") : "-"}
                  </td>
                  <td className="text-gray-900">{l.user_name || `#${l.user_id}`}</td>
                  <td>
                    <span className="px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-800 font-mono">
                      {l.action}
                    </span>
                  </td>
                  <td className="text-gray-600">
                    {l.entity}{l.entity_id ? `#${l.entity_id}` : ""}
                  </td>
                  <td className="text-gray-700">{l.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
