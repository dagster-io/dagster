-- WARNING: This query is an example of what NOT to do. It exposes sensitive user information.
SELECT 
    u.user_id,
    u.name,
    u.email,
    i.invoice_id,
    i.amount,
    i.status
FROM 
    payment.public.users u
JOIN 
    payment.public.invoices i ON u.user_id = i.payer_user_id;