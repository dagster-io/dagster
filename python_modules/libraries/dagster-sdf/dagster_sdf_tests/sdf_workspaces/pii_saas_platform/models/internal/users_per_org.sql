SELECT o.organization_id, o.name, COUNT(u.user_id) AS user_count
FROM payment.public.organizations  o
JOIN payment.public.users u ON o.organization_id = u.organization_id
GROUP BY o.organization_id, o.name;
