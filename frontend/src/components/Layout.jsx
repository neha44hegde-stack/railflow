import { Link, NavLink, useNavigate } from "react-router-dom";
import { Train, LogOut, FileText } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const nav = useNavigate();

  const linkCls = ({ isActive }) =>
    `px-3 py-2 rounded-md text-sm font-medium ${isActive ? "bg-navy-800 text-white" : "text-gray-700 hover:bg-gray-100"}`;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-navy-900 text-white">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-lg font-bold">
            <Train size={22} /> RAILFLOW
          </Link>
          <nav className="flex items-center gap-2">
            {user ? (
              <>
                {user.role === "PASSENGER" && (
                  <>
                    <NavLink to="/search" className={linkCls}>Search</NavLink>
                    <NavLink to="/bookings" className={linkCls}>My Bookings</NavLink>
                    <NavLink to="/pnr" className={linkCls}>PNR Status</NavLink>
                  </>
                )}
                {user.role === "ADMIN" && (
                  <>
                    <NavLink to="/admin" end className={linkCls}>Dashboard</NavLink>
                    <NavLink to="/admin/stations" className={linkCls}>Stations</NavLink>
                    <NavLink to="/admin/trains" className={linkCls}>Trains</NavLink>
                    <NavLink to="/admin/bookings" className={linkCls}>Bookings</NavLink>
                    <NavLink to="/admin/users" className={linkCls}>Users</NavLink>
                    <NavLink to="/admin/audit" className={linkCls}>
                      <span className="inline-flex items-center gap-1"><FileText size={14}/>Audit</span>
                    </NavLink>
                  </>
                )}
                <span className="text-sm text-gray-300 ml-2">{user.name}</span>
                <button onClick={() => { logout(); nav("/login"); }}
                        className="ml-2 text-gray-300 hover:text-white" title="Logout">
                  <LogOut size={18} />
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="px-3 py-2 text-sm hover:bg-navy-800 rounded-md">Login</Link>
                <Link to="/register" className="px-3 py-2 text-sm bg-rail-600 hover:bg-rail-500 rounded-md">Register</Link>
              </>
            )}
          </nav>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
