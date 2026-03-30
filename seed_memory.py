import asyncio
from vanna_setup import agent

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
    ("Top 5 patients", "SELECT p.first_name, SUM(i.total_amount) FROM patients p JOIN invoices i ON p.id=i.patient_id GROUP BY p.id ORDER BY SUM(i.total_amount) DESC LIMIT 5"),
    ("Show revenue by doctor", "SELECT d.name, SUM(i.total_amount) as total_revenue FROM invoices i JOIN appointments a ON a.patient_id=i.patient_id JOIN doctors d ON d.id=a.doctor_id GROUP BY d.id ORDER BY total_revenue DESC"),
    ("Which city has the most patients?", "SELECT city, COUNT(*) as patient_count FROM patients GROUP BY city ORDER BY patient_count DESC LIMIT 1"),
    ("Count doctors by specialization", "SELECT specialization, COUNT(*) as doctor_count FROM doctors GROUP BY specialization"),
    ("Monthly appointment trends", "SELECT strftime('%Y-%m', appointment_date) as month, COUNT(*) as appointment_count FROM appointments GROUP BY month ORDER BY month DESC"),
    ("Average treatment cost", "SELECT AVG(cost) as avg_cost FROM treatments"),
]

async def seed():
    class Ctx:
        metadata = {}

    print("Seeding...")

    for q, s in data:
        try:
            res = agent.send_message(
                message=f"Remember: {q} -> {s}",
                request_context=Ctx()
            )

            async for _ in res:
                pass

            print("Added:", q)

        except:
            # ignore errors (important)
            print("Skipped:", q)

    print("Done")

if __name__ == "__main__":
    asyncio.run(seed())