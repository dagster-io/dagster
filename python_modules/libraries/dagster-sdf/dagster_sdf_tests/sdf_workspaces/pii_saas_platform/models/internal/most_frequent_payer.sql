SELECT 
    o.organization_id,
    o.name AS organization_name,
    u.user_id,
    u.email,
    COUNT(i.invoice_id) AS payment_count
FROM 
    payment.public.invoices i
JOIN 
    payment.public.users u ON i.payer_user_id = u.user_id
JOIN 
    payment.public.organizations o ON u.organization_id = o.organization_id
WHERE 
    i.status = 'Paid' -- Considering only paid invoices
GROUP BY 
    o.organization_id, o.name, u.user_id, u.email
ORDER BY 
    o.organization_id, payment_count DESC;
