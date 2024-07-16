SELECT 
    o.organization_id,
    o.name AS organization_name,
    COUNT(i.invoice_id) AS total_invoices,
    AVG(i.amount) AS average_invoice_amount,
    SUM(CASE WHEN i.status = 'Paid' THEN 1 ELSE 0 END) / COUNT(i.invoice_id) * 100 AS percent_invoices_paid
FROM 
    payment.public.organizations o
LEFT JOIN 
    payment.public.invoices i ON o.organization_id = i.organization_id
GROUP BY 
    o.organization_id, o.name;