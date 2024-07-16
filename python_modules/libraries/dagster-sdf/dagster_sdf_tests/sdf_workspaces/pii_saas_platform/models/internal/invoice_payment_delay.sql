SELECT invoice_id, DATEDIFF(day, due_date, paid_date) AS delay_days
FROM payment.public.invoices 
WHERE status = 'Paid' AND paid_date > due_date;

