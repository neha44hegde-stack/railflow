import { Link } from "react-router-dom";
import { Train, Ticket, Search, ShieldCheck } from "lucide-react";

export default function Landing() {
  return (
    <div className="py-10">
      <div className="text-center mb-12">
        <Train size={56} className="mx-auto text-rail-600" />
        <h1 className="text-4xl font-bold text-navy-900 mt-4">RailFlow</h1>
        <p className="text-gray-600 mt-2">Train management & ticket booking, end to end.</p>
        <div className="mt-6 flex justify-center gap-3">
          <Link to="/search" className="px-5 py-2 bg-rail-600 text-white rounded-md hover:bg-rail-500">Search Trains</Link>
          <Link to="/pnr" className="px-5 py-2 border border-gray-300 rounded-md hover:bg-gray-100">Check PNR</Link>
        </div>
      </div>
      <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
        {[
          { icon: Search, title: "Search & Book", text: "Search by route and date, pick a class and book instantly." },
          { icon: Ticket, title: "Instant PNR", text: "Get a real PNR backed by database transactions." },
          { icon: ShieldCheck, title: "Secure", text: "JWT auth, hashed passwords, role-based access." },
        ].map(({ icon: Icon, title, text }) => (
          <div key={title} className="bg-white border border-gray-200 rounded-lg p-6">
            <Icon className="text-rail-600" />
            <h3 className="font-semibold text-navy-900 mt-3">{title}</h3>
            <p className="text-sm text-gray-600 mt-1">{text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
