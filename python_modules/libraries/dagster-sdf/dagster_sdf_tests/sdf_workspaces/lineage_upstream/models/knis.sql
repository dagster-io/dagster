select txn_date, sum(qty) as qty
from middle
group by txn_date