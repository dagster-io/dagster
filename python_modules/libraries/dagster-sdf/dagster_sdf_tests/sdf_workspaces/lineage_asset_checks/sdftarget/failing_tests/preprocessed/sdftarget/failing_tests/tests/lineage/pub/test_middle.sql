

WITH
middle_constraints AS (
    SELECT
        CASE WHEN NOT(COUNT(CASE WHEN phone LIKE 'non_existent_%' THEN 1 ELSE NULL END)>0) 
	THEN 
	'err: column phone has strings that are NOT like ''non_existent_%''' ELSE NULL END AS phone_1
        ,
        CASE WHEN COUNT(CASE WHEN phone NOT IN ('non_existent') THEN 1 ELSE NULL END) > 0 
    THEN  
    'err: column phone has values outside accepted values ''non_existent''' ELSE NULL END AS phone_2
    FROM lineage.pub.middle
)
,middle_user_id_user_id AS (
    SELECT
        'err: columns "user_id", "user_id" are NOT unique' AS reason
    FROM (SELECT "user_id", "user_id" 
          FROM middle
          GROUP BY "user_id", "user_id"
          HAVING COUNT(*) > 1) _subquery
)

SELECT reason 
FROM (
   
    SELECT phone_1 as reason FROM middle_constraints WHERE phone_1 IS NOT NULL
    UNION ALL
       
    SELECT phone_2 as reason FROM middle_constraints WHERE phone_2 IS NOT NULL 
    
    UNION ALL
    SELECT reason FROM middle_user_id_user_id
 
    ) AS _combined_errors
ORDER BY reason;
