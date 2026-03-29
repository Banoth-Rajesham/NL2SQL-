import asyncio
from vanna_setup import agent

# ---------- QUESTIONS + SQL ----------
data = [
    ("How many patients do we have?", "SELECT COUNT(*) FROM patients"),
    ("List patients in Hyderabad", "SELECT * FROM patients WHERE city='Hyderabad'"),
    ("How many female patients?", "SELECT COUNT(*) FROM patients WHERE gender='F'"),

    ("List doctors in Cardiology", "SELECT * FROM doctors WHERE specialization='Cardiology'"),
    ("Who is the busiest doctor?", "SELECT d.name, COUNT(a.id) FROM doctors d JOIN appointments a ON d.id=a.doctor_id GROUP BY d.id ORDER BY COUNT(a.id) DESC LIMIT 1"),

    ("Show appointments by status", "SELECT status, COUNT(*) FROM appointments GROUP BY status"),
    ("Appointments last month", "SELECT * FROM appointments WHERE appointment_date >= date('now','-1 month')"),

    ("Total revenue", "SELECT SUM(total_amount) FROM invoices"),
    ("Unpaid invoices", "SELECT * FROM invoices WHERE status!='Paid'"),

    ("Top 5 patients by spending", "SELECT p.first_name, SUM(i.total_amount) FROM patients p JOIN invoices i ON p.id=i.patient_id GROUP BY p.id ORDER BY SUM(i.total_amount) DESC LIMIT 5"),

    ("Monthly appointments", "SELECT strftime('%Y-%m', appointment_date), COUNT(*) FROM appointments GROUP BY 1"),
    ("Revenue by month", "SELECT strftime('%Y-%m', invoice_date), SUM(total_amount) FROM invoices GROUP BY 1")
]

# ---------- FUNCTION ----------
async def seed():

    # simple context (required by Vanna)
    class Ctx:
        metadata = {}

    for q, s in data:
        res = agent.send_message(
            message=f"Question: {q} SQL: {s}",
            request_context=Ctx()
        )

        # run silently
        async for _ in res:
            pass

        print("Added:", q)

# ---------- RUN ----------
if __name__ == "__main__":
    asyncio.run(seed())
    print("Done seeding 👍")