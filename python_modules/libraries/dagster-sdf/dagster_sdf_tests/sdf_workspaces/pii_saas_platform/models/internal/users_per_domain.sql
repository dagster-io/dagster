SELECT 
    o.organization_id,
    o.name AS organization_name,
    SPLIT_PART(u.email, '@', 2) AS email_domain,
    COUNT(*) AS user_count
FROM 
    payment.public.users u
JOIN 
    payment.public.organizations o ON u.organization_id = o.organization_id
GROUP BY 
    o.organization_id, o.name, email_domain
ORDER BY 
    o.organization_id, user_count DESC;
