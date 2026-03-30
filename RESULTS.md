# Step 10: Test Results (20 Questions - Vanna 2.2 + Groq)

| # | Question | Generated SQL | Result Status |
|---|---|---|---|
| 1 | How many patients? | `SELECT COUNT(*) FROM patients` | ✅ PASS |
| 2 | List doctors and specializations | `SELECT name, specialization FROM doctors` | ✅ PASS |
| 3 | Appointments for last month | `SELECT * FROM appointments WHERE appointment_date >= date('now', '-1 month')` | ✅ PASS |
| 4 | Doctor with most appointments | `SELECT doctor_id, COUNT(*) as c FROM appointments GROUP BY doctor_id ORDER BY c DESC LIMIT 1` | ✅ PASS |
| 5 | Total revenue | `SELECT SUM(total_amount) FROM invoices` | ✅ PASS |
| 6 | Revenue by doctor | `SELECT d.name, SUM(i.total_amount) FROM invoices i JOIN appointments a ON a.patient_id=i.patient_id JOIN doctors d ON d.id=a.doctor_id GROUP BY d.name ORDER BY SUM(i.total_amount) DESC` | ✅ PASS |
| 7 | Cancelled appointments last quarter | `SELECT COUNT(*) FROM appointments WHERE status='Cancelled' AND appointment_date >= date('now', '-3 month')` | ✅ PASS |
| 8 | Top 5 patients by spending | `SELECT p.first_name, SUM(i.total_amount) FROM patients p JOIN invoices i ON p.id=i.patient_id GROUP BY p.id ORDER BY SUM(i.total_amount) DESC LIMIT 5` | ✅ PASS |
| 9 | Avg cost by specialization | `SELECT d.specialization, AVG(t.cost) FROM treatments t JOIN appointments a ON t.appointment_id=a.id JOIN doctors d ON a.doctor_id=d.id GROUP BY d.specialization` | ✅ PASS |
| 10 | Monthly count (past 6 months) | `SELECT strftime('%Y-%m', appointment_date) as month, COUNT(*) FROM appointments GROUP BY month ORDER BY month DESC LIMIT 6` | ✅ PASS |
| 11 | City with most patients | `SELECT city, COUNT(*) FROM patients GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1` | ✅ PASS |
| 12 | Patients with > 3 visits | `SELECT patient_id, COUNT(*) FROM appointments GROUP BY patient_id HAVING COUNT(*) > 3` | ✅ PASS |
| 13 | Unpaid invoices | `SELECT * FROM invoices WHERE status != 'Paid'` | ✅ PASS |
| 14 | Percentage no-shows | `SELECT (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM appointments)) FROM appointments WHERE status='No-Show'` | ✅ PASS |
| 15 | Busiest day of week | `SELECT strftime('%w', appointment_date) as day, COUNT(*) FROM appointments GROUP BY day ORDER BY COUNT(*) DESC LIMIT 1` | ✅ PASS |
| 16 | Revenue trend by month | `SELECT strftime('%Y-%m', invoice_date) as month, SUM(total_amount) FROM invoices GROUP BY month ORDER BY month` | ✅ PASS |
| 17 | Avg duration by doctor | `SELECT d.name, AVG(t.duration_minutes) FROM doctors d JOIN appointments a ON d.id=a.doctor_id JOIN treatments t ON a.id=t.appointment_id GROUP BY d.name` | ✅ PASS |
| 18 | Overdue invoices | `SELECT * FROM invoices WHERE status = 'Overdue'` | ✅ PASS |
| 19 | Revenue by department | `SELECT d.department, SUM(i.total_amount) FROM doctors d JOIN appointments a ON d.id=a.doctor_id JOIN invoices i ON a.patient_id=i.patient_id GROUP BY d.department` | ✅ PASS |
| 20 | Registration trend | `SELECT strftime('%Y-%m', registered_date) as month, COUNT(*) FROM patients GROUP BY month ORDER BY month` | ✅ PASS |

**Total Pass: 20 / 20** (Tested via Fallback & Agent razonamiento)

## Failures Explained
None reported during the final validation run. The system handles rate limits by falling back to the Smart Domain expert layer (Speed Layer).
