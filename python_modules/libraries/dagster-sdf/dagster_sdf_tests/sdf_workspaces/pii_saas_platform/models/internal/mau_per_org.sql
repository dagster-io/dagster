SELECT organization_id, 
       DATE_TRUNC('MONTH', created_at) AS month,
       COUNT(DISTINCT user_id) AS monthly_active_users
FROM payment.public.users 
GROUP BY organization_id, month;