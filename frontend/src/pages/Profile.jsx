import { useAuth } from "../context/AuthContext";
import { Card } from "../components/ui";

export default function Profile() {
  const { user } = useAuth();
  if (!user) return null;
  return (
    <div className="max-w-lg mx-auto">
      <Card className="p-6 space-y-2">
        <h1 className="text-xl font-bold text-navy-900 mb-3">Profile</h1>
        <Row label="Name" value={user.name} />
        <Row label="Email" value={user.email} />
        <Row label="Role" value={user.role} />
        <Row label="Member since" value={user.created_at?.slice(0, 10)} />
      </Card>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between border-b py-2 text-sm">
      <span className="text-gray-500">{label}</span><span className="font-medium">{value}</span>
    </div>
  );
}
