## Jaffle Shop Analytics

### Orders

```sql orders_by_day
select * from orders_by_day
```

<BarChart
  title="Orders by Day"
  data={orders_by_day}
  x="order_date"
  y="order_count"
/>

<LineChart
  title="Revenue by Day"
  data={orders_by_day}
  x="order_date"
  y="total_amount"
  yFmt="usd"
/>

### Customers

```sql customers
select ifnull(customer_lifetime_value, 0) as customer_lifetime_value from customers
```

<Histogram
  title="Customer Lifetime Value"
  data={customers}
  x="customer_lifetime_value"
  xFmt="usd"
/>
