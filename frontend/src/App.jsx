import { lazy, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import SearchPage from "./pages/SearchPage";
import BookingPage from "./pages/BookingPage";
import MyBookings from "./pages/MyBookings";
import PnrStatus from "./pages/PnrStatus";
import TicketPage from "./pages/TicketPage";
import Profile from "./pages/Profile";

const AdminDashboard = lazy(() => import("./pages/admin/AdminDashboard"));
const AdminStations = lazy(() => import("./pages/admin/AdminStations"));
const AdminTrains = lazy(() => import("./pages/admin/AdminTrains"));
const AdminTrainDetail = lazy(() => import("./pages/admin/AdminTrainDetail"));
const AdminBookings = lazy(() => import("./pages/admin/AdminBookings"));
const AdminUsers = lazy(() => import("./pages/admin/AdminUsers"));
const AdminAuditLog = lazy(() => import("./pages/admin/AdminAuditLog"));

const Fallback = () => <div className="p-8 text-gray-500 text-center text-sm">Loading...</div>;

export default function App() {
  return (
    <Layout>
      <Suspense fallback={<Fallback />}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route path="/search" element={<ProtectedRoute role="PASSENGER"><SearchPage /></ProtectedRoute>} />
          <Route path="/book/:trainId" element={<ProtectedRoute role="PASSENGER"><BookingPage /></ProtectedRoute>} />
          <Route path="/bookings" element={<ProtectedRoute role="PASSENGER"><MyBookings /></ProtectedRoute>} />
          <Route path="/pnr" element={<PnrStatus />} />
          <Route path="/ticket/:pnr" element={<ProtectedRoute><TicketPage /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />

          <Route path="/admin" element={<ProtectedRoute role="ADMIN"><AdminDashboard /></ProtectedRoute>} />
          <Route path="/admin/stations" element={<ProtectedRoute role="ADMIN"><AdminStations /></ProtectedRoute>} />
          <Route path="/admin/trains" element={<ProtectedRoute role="ADMIN"><AdminTrains /></ProtectedRoute>} />
          <Route path="/admin/trains/:id" element={<ProtectedRoute role="ADMIN"><AdminTrainDetail /></ProtectedRoute>} />
          <Route path="/admin/bookings" element={<ProtectedRoute role="ADMIN"><AdminBookings /></ProtectedRoute>} />
          <Route path="/admin/users" element={<ProtectedRoute role="ADMIN"><AdminUsers /></ProtectedRoute>} />
          <Route path="/admin/audit" element={<ProtectedRoute role="ADMIN"><AdminAuditLog /></ProtectedRoute>} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </Layout>
  );
}
