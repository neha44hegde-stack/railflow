// Format "HH:MM" (24h) as "h:MM AM/PM". Returns "--" if missing.
export function format12h(t) {
  if (!t) return "--";
  const parts = String(t).split(":");
  if (parts.length < 2) return t;
  const h = parseInt(parts[0], 10);
  const m = parseInt(parts[1], 10);
  if (isNaN(h) || isNaN(m)) return t;
  const ampm = h < 12 ? "AM" : "PM";
  const h12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
  return `${h12}:${String(m).padStart(2, "0")} ${ampm}`;
}
