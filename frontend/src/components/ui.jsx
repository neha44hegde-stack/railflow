import { Loader2 } from "lucide-react";

export function Button({ children, variant = "primary", className = "", ...props }) {
  const base = "px-4 py-2 rounded-md font-medium transition disabled:opacity-50 disabled:cursor-not-allowed";
  const styles = {
    primary: "bg-rail-600 text-white hover:bg-rail-500",
    neutral: "bg-gray-100 text-gray-800 hover:bg-gray-200",
    danger:  "bg-red-600 text-white hover:bg-red-500",
    outline: "border border-gray-300 text-gray-700 hover:bg-gray-50",
  };
  return <button className={`${base} ${styles[variant]} ${className}`} {...props}>{children}</button>;
}

export function Card({ children, className = "" }) {
  return <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>{children}</div>;
}

export function Spinner({ label = "Loading…" }) {
  return (
    <div className="flex items-center gap-2 text-gray-500 py-6">
      <Loader2 className="animate-spin" size={18} /> {label}
    </div>
  );
}

export function ErrorBox({ message }) {
  if (!message) return null;
  return <div className="bg-red-50 text-red-700 border border-red-200 rounded-md p-3 text-sm">{message}</div>;
}

export function Empty({ message }) {
  return <div className="text-center text-gray-500 py-8">{message}</div>;
}
