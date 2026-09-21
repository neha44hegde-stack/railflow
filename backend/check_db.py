import sqlite3, os

path = os.path.join("instance", "railflow_dev.db")
c = sqlite3.connect(path)

cols = [r[1] for r in c.execute("PRAGMA table_info(bookings)").fetchall()]
print("bookings columns:")
for col in cols:
    print("  -", col)

print()
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("tables:", tables)

print()
has_status = "booking_status" in cols
has_wl = "waitlist_position" in cols
has_audit = "audit_logs" in tables

print("booking_status     :", has_status)
print("waitlist_position  :", has_wl)
print("audit_logs table   :", has_audit)

if not (has_status and has_wl and has_audit):
    print()
    print("MIGRATION INCOMPLETE - run this to fix:")
    if not has_status:
        print("  ALTER TABLE bookings ADD COLUMN booking_status VARCHAR(10) DEFAULT 'CNF';")
    if not has_wl:
        print("  ALTER TABLE bookings ADD COLUMN waitlist_position INTEGER;")
    if not has_audit:
        print("  CREATE TABLE audit_logs (...);")