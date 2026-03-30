import asyncio
import logging
from vanna_setup import agent, make_request_context

# Training data (Step 5 requirements)
training_data = [
    # Patients
    ("How many patients do we have?", "SELECT COUNT(*) as total_patients FROM patients"),
    ("How many female patients?", "SELECT COUNT(*) as females FROM patients WHERE gender='F'"),
    ("List patients in Hyderabad", "SELECT * FROM patients WHERE city='Hyderabad'"),
    # Doctors
    ("List all doctors and their specializations", "SELECT name, specialization, department FROM doctors"),
    ("Who is the busiest doctor?", "SELECT d.name, COUNT(a.id) as appt_count FROM doctors d JOIN appointments a ON d.id=a.doctor_id GROUP BY d.id ORDER BY appt_count DESC LIMIT 1"),
    # Appointments
    ("Show me appointments for last month", "SELECT * FROM appointments WHERE appointment_date >= date('now', '-1 month')"),
    ("How many cancelled appointments last quarter?", "SELECT COUNT(*) FROM appointments WHERE status='Cancelled' AND appointment_date >= date('now', '-3 month')"),
    ("Show monthly appointment count for the past 6 months", "SELECT strftime('%Y-%m', appointment_date) as month, COUNT(*) as count FROM appointments GROUP BY month ORDER BY month DESC LIMIT 6"),
    # Financials
    ("What is the total revenue?", "SELECT SUM(total_amount) as total_revenue FROM invoices"),
    ("Show revenue by doctor", "SELECT d.name, SUM(i.total_amount) as revenue FROM invoices i JOIN appointments a ON a.patient_id=i.patient_id JOIN doctors d ON d.id=a.doctor_id GROUP BY d.id ORDER BY revenue DESC"),
    ("Show unpaid invoices", "SELECT * FROM invoices WHERE status != 'Paid' LIMIT 15"),
    ("Average treatment cost by specialization", "SELECT d.specialization, AVG(t.cost) as avg_cost FROM treatments t JOIN appointments a ON t.appointment_id=a.id JOIN doctors d ON a.doctor_id=d.id GROUP BY d.specialization"),
    # Trends
    ("Which city has the most patients?", "SELECT city, COUNT(*) as count FROM patients GROUP BY city ORDER BY count DESC LIMIT 1"),
    ("Top 5 patients by spending", "SELECT p.first_name, p.last_name, SUM(i.total_amount) as spending FROM patients p JOIN invoices i ON p.id=i.patient_id GROUP BY p.id ORDER BY spending DESC LIMIT 5"),
    ("Revenue trend by month", "SELECT strftime('%Y-%m', invoice_date) as month, SUM(total_amount) as revenue FROM invoices GROUP BY month ORDER BY month DESC")
]

async def seed():
    print("🚀 Seeding Agent Memory (Vanna 2.0)...")
    ctx = make_request_context({"env": "seed"})
    
    for i, (q, sql) in enumerate(training_data):
        print(f"[{i+1}/15] Seeding: {q}")
        try:
            # Inform the agent: "This is the correct SQL for this question"
            # In Vanna 2.2+, the agent learns from "Remember: <Question> -> <SQL>" in the message
            # if we have the SaveQuestionToolArgsTool registered.
            prompt = f"Remember this mapping for future queries: \nQuestion: {q}\nCorrect SQL: {sql}"
            
            # Use async stream to ensure it's processed
            async for component in agent.send_message(ctx, prompt):
                pass # Consume stream to finish processing
            
        except Exception as e:
            print(f"  Failed: {e}")
            
    print("✅ Memory Seeding Complete. 15 items added to DemoAgentMemory.")

if __name__ == "__main__":
    asyncio.run(seed())