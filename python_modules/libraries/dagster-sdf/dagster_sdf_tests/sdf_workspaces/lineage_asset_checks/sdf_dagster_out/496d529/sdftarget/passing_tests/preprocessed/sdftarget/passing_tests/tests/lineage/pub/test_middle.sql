

WITH
middle_constraints AS (
    SELECT
        CASE WHEN COUNT(CASE WHEN phone IS NULL THEN 1 ELSE NULL END) > 0 
    THEN  
    'err: column phone has NULL values' ELSE NULL END AS phone_1
    FROM lineage.pub.middle
)
,middle_user_id_phone AS (
    SELECT
        'err: columns "user_id", "phone" are NOT unique' AS reason
    FROM (SELECT "user_id", "phone" 
          FROM middle
          GROUP BY "user_id", "phone"
          HAVING COUNT(*) > 1) _subquery
)

SELECT reason 
FROM (
   
    SELECT phone_1 as reason FROM middle_constraints WHERE phone_1 IS NOT NULL 
    
    UNION ALL
    SELECT reason FROM middle_user_id_phone
 
    ) AS _combined_errors
ORDER BY reason;
