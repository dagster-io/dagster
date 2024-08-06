select user_id, max(phone) as phone, txn_date, sum(qty) as qty 
from source
group by user_id, txn_date