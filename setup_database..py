import sqlite3, random
from datetime import datetime, timedelta

# ---------- CONNECT ----------
conn = sqlite3.connect("clinic.db")
cur = conn.cursor()

# ---------- CREATE TABLES ----------
cur.execute("CREATE TABLE IF NOT EXISTS patients (id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT, phone TEXT, date_of_birth TEXT, gender TEXT, city TEXT, registered_date TEXT)")

cur.execute("CREATE TABLE IF NOT EXISTS doctors (id INTEGER PRIMARY KEY, name TEXT, specialization TEXT, department TEXT, phone TEXT)")

cur.execute("CREATE TABLE IF NOT EXISTS appointments (id INTEGER PRIMARY KEY, patient_id INTEGER, doctor_id INTEGER, appointment_date TEXT, status TEXT, notes TEXT)")

cur.execute("CREATE TABLE IF NOT EXISTS treatments (id INTEGER PRIMARY KEY, appointment_id INTEGER, treatment_name TEXT, cost REAL, duration_minutes INTEGER)")

cur.execute("CREATE TABLE IF NOT EXISTS invoices (id INTEGER PRIMARY KEY, patient_id INTEGER, invoice_date TEXT, total_amount REAL, paid_amount REAL, status TEXT)")

# ---------- HELPERS ----------
def rand_date(days=365):
    return (datetime.now() - timedelta(days=random.randint(0, days))).strftime("%Y-%m-%d")

cities = ["Hyd", "Mumbai", "Delhi", "Chennai", "BLR"]
specs = ["Cardio", "Derm", "Ortho", "Pedia", "General"]

# ---------- DOCTORS ----------
for i in range(1, 16):
    cur.execute("INSERT INTO doctors VALUES (NULL, ?, ?, ?, ?)", 
                (f"Dr{i}", specs[i % 5], specs[i % 5], f"9000{i:04d}"))

# ---------- PATIENTS ----------
for i in range(1, 201):
    cur.execute("INSERT INTO patients VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)", (
        f"F{i}", f"L{i}",
        f"u{i}@mail.com" if i % 10 else None,
        f"9999{i:04d}" if i % 15 else None,
        rand_date(8000),
        random.choice(["M", "F"]),
        random.choice(cities),
        rand_date()
    ))

# ---------- APPOINTMENTS ----------
for _ in range(500):
    cur.execute("INSERT INTO appointments VALUES (NULL, ?, ?, ?, ?, ?)", (
        random.randint(1, 200),
        random.randint(1, 15),
        rand_date(),
        random.choice(["Completed", "Cancelled", "Scheduled", "No-Show"]),
        "note" if random.choice([0,1]) else None
    ))

# ---------- TREATMENTS ----------
ids = [r[0] for r in cur.execute("SELECT id FROM appointments WHERE status='Completed'")]

for _ in range(350):
    cur.execute("INSERT INTO treatments VALUES (NULL, ?, ?, ?, ?)", (
        random.choice(ids) if ids else random.randint(1, 500),
        f"T{random.randint(1,5)}",
        random.randint(50, 5000),
        random.choice([15,30,45,60])
    ))

# ---------- INVOICES ----------
for _ in range(300):
    total = random.randint(50, 5000)
    status = random.choice(["Paid", "Pending", "Overdue"])
    paid = total if status == "Paid" else random.randint(0, total)

    cur.execute("INSERT INTO invoices VALUES (NULL, ?, ?, ?, ?, ?)", (
        random.randint(1, 200),
        rand_date(),
        total,
        paid,
        status
    ))

# ---------- SAVE ----------
conn.commit()
conn.close()

print("Done 👍")