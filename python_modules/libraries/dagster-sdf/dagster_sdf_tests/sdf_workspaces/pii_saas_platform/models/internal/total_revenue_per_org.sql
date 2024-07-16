SELECT organization_id, SUM(amount) AS total_revenue
FROM payment.public.invoices 
WHERE status = 'Paid'
GROUP BY organization_id;
