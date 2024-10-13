view: omni_channel_transactions {
  derived_table: {
   datagroup_trigger: new_day
    sql:
      -- adding comment to trigger pdt rebuild
      SELECT *
      FROM
      (
      SELECT
      purchase_channel,
      fulfillment_channel,
      transaction_date,
      shipped_date,
      delivered_date,
      returned_date,
      transaction_id,
      store_name,
      store_latitude,
      store_longitude,
      store_state,
      Store_sq_ft,
      CASE  WHEN rand() < 0.5 THEN null
            WHEN rand() < 0.5 AND fulfillment_channel = 'Delivery' THEN 'Free Delivery'
            WHEN rand() < 0.5 THEN 'Single Item Discount'
            WHEN rand() < 0.5 THEN 'BOGO'
            WHEN rand() < 0.5 THEN 'Free Item'
            WHEN rand() < 0.5 THEN 'Frequency Discount'
            WHEN rand() < 0.5 THEN 'Multi-Item Discount'
            ELSE 'Order Discount'
      END AS offer_type,
      CAST(ROUND(RAND()*85225 + 1.0,0) AS INT64) as customer_id,
      ARRAY_AGG(STRUCT(gross_margin,sale_price,product_category,product_brand,product_department,product_area,product_name,product_sku)) as transaction_details
      FROM
      (
      SELECT
        IF(channels.NAME in ('In-store Self-checkout','In-store Tills'),'In-store','Online')  AS purchase_channel,
        CASE
          WHEN channels.NAME = 'In-store Self-checkout' THEN 'Self Checkout'
          WHEN channels.NAME = 'In-store Tills' THEN 'Assisted Checkout'
          WHEN channels.NAME in ('Click and Collect','Online') THEN 'In-store Pickup'
         END AS fulfillment_channel,
        transactions__line_items.gross_margin  AS gross_margin,
        transactions__line_items.sale_price * 1.2  AS sale_price,
        transactions.transaction_timestamp AS transaction_date,
        null as delivered_date,
        null as shipped_date,
        if(rand() < 0.02, TIMESTAMP_ADD(transaction_timestamp, INTERVAL cast(round(rand()*30,0) as INT64) DAY),null) as returned_date,
        transactions.transaction_id  AS transaction_id,
        stores.NAME AS store_name,
        stores.LATITUDE as store_latitude,
        stores.LONGITUDE as store_longitude,
        stores.State  AS store_state,
        stores.sq_ft  AS store_sq_ft,
        products.CATEGORY  AS product_category,
        products.BRAND  AS product_brand,
        CASE
            WHEN products.CATEGORY IN ('Accessories', 'Swim', 'Socks', 'Socks & Hosiery', 'Leggings', 'Plus', 'Sleep & Lounge') THEN 'Accessories'
            WHEN products.CATEGORY IN ('Jeans', 'Tops & Tees', 'Shorts', 'Sweaters', 'Underwear', 'Intimates', 'Jumpsuits & Rompers', 'Maternity') THEN 'Casual Wear'
            WHEN products.CATEGORY IN ('Dresses', 'Skirts', 'Blazers & Jackets', 'Pants', 'Pants & Capris', 'Suits') THEN 'Formal Wear'
            WHEN products.CATEGORY IN ('Clothing Sets', 'Suits & Sport Coats', 'Outerwear & Coats', 'Fashion Hoodies & Sweatshirts', 'Suits', 'Active') THEN 'Outerwear'
            ELSE 'Other'
          END AS product_area,
        products.NAME  AS product_name,
        products.SKU  AS product_sku,
        products.DEPARTMENT  AS product_department,
      FROM `looker-private-demo.retail.transaction_detail`  AS transactions
      LEFT JOIN UNNEST((
          transactions.line_items
      )) as transactions__line_items
      LEFT JOIN `looker-private-demo.retail.products`  AS products ON products.ID = transactions__line_items.product_id
      LEFT JOIN `looker-private-demo.retail.us_stores` AS stores ON stores.ID = transactions.store_id
      LEFT JOIN `looker-private-demo.retail.channels`  AS channels ON channels.ID = transactions.channel_id

      UNION ALL

      SELECT
        IF(channels.NAME in ('In-store Self-checkout','In-store Tills'),'In-store','Online')  AS purchase_channel,
        CASE
          WHEN channels.NAME = 'In-store Self-checkout' THEN 'Self Checkout'
          WHEN channels.NAME = 'In-store Tills' THEN 'Assisted Checkout'
          WHEN channels.NAME in ('Click and Collect','Online') THEN 'In-store Pickup'
         END AS fulfillment_channel,
        Transactions__line_items.gross_margin * 1.1  AS gross_margin,
        transactions__line_items.sale_price  AS sale_price,
        TIMESTAMP_SUB(CURRENT_TIMESTAMP, INTERVAL CAST(ROUND(RAND()*388800,0) AS INT64) MINUTE) AS transaction_date,
        null as delivered_date,
        null as shipped_date,
        null as returned_date,
        transactions.transaction_id  AS transaction_id,
        stores.NAME AS store_name,
        stores.LATITUDE as store_latitude,
        stores.LONGITUDE as store_longitude,
        stores.State  AS store_state,
        stores.sq_ft  AS store_sq_ft,
        products.CATEGORY  AS product_category,
        products.BRAND  AS product_brand,
        CASE
            WHEN products.CATEGORY IN ('Accessories', 'Swim', 'Socks', 'Socks & Hosiery', 'Leggings', 'Plus', 'Sleep & Lounge') THEN 'Accessories'
            WHEN products.CATEGORY IN ('Jeans', 'Tops & Tees', 'Shorts', 'Sweaters', 'Underwear', 'Intimates', 'Jumpsuits & Rompers', 'Maternity') THEN 'Casual Wear'
            WHEN products.CATEGORY IN ('Dresses', 'Skirts', 'Blazers & Jackets', 'Pants', 'Pants & Capris', 'Suits') THEN 'Formal Wear'
            WHEN products.CATEGORY IN ('Clothing Sets', 'Suits & Sport Coats', 'Outerwear & Coats', 'Fashion Hoodies & Sweatshirts', 'Suits', 'Active') THEN 'Outerwear'
            ELSE 'Other'
          END AS product_area,
        products.NAME  AS product_name,
        products.SKU  AS product_sku,
        products.DEPARTMENT  AS product_department,
      FROM `looker-private-demo.retail.transaction_detail`  AS transactions
      LEFT JOIN UNNEST((
          transactions.line_items
      )) as transactions__line_items
      LEFT JOIN `looker-private-demo.retail.products`  AS products ON products.ID = transactions__line_items.product_id
      LEFT JOIN `looker-private-demo.retail.us_stores` AS stores ON stores.ID = transactions.store_id
      LEFT JOIN `looker-private-demo.retail.channels`  AS channels ON channels.ID = transactions.channel_id
      WHERE channels.NAME not in ('In-store Self-checkout','In-store Tills')

      UNION ALL

      SELECT
        IF(channels.NAME in ('In-store Self-checkout','In-store Tills'),'In-store','Online')  AS purchase_channel,
        CASE
          WHEN channels.NAME = 'In-store Self-checkout' THEN 'Self Checkout'
          WHEN channels.NAME = 'In-store Tills' THEN 'Assisted Checkout'
          WHEN channels.NAME in ('Click and Collect','Online') THEN 'In-store Pickup'
         END AS fulfillment_channel,
        transactions__line_items.gross_margin  AS gross_margin,
        transactions__line_items.sale_price * 1.2  AS sale_price,
        transactions.transaction_timestamp AS transaction_date,
        null as delivered_date,
        null as shipped_date,
        null as returned_date,
        transactions.transaction_id  AS transaction_id,
        stores.NAME AS store_name,
        stores.LATITUDE as store_latitude,
        stores.LONGITUDE as store_longitude,
        stores.State  AS store_state,
        stores.sq_ft  AS store_sq_ft,
        products.CATEGORY  AS product_category,
        products.BRAND  AS product_brand,
        CASE
            WHEN products.CATEGORY IN ('Accessories', 'Swim', 'Socks', 'Socks & Hosiery', 'Leggings', 'Plus', 'Sleep & Lounge') THEN 'Accessories'
            WHEN products.CATEGORY IN ('Jeans', 'Tops & Tees', 'Shorts', 'Sweaters', 'Underwear', 'Intimates', 'Jumpsuits & Rompers', 'Maternity') THEN 'Casual Wear'
            WHEN products.CATEGORY IN ('Dresses', 'Skirts', 'Blazers & Jackets', 'Pants', 'Pants & Capris', 'Suits') THEN 'Formal Wear'
            WHEN products.CATEGORY IN ('Clothing Sets', 'Suits & Sport Coats', 'Outerwear & Coats', 'Fashion Hoodies & Sweatshirts', 'Suits', 'Active') THEN 'Outerwear'
            ELSE 'Other'
          END AS product_area,
        products.NAME  AS product_name,
        products.SKU  AS product_sku,
        products.DEPARTMENT  AS product_department,
      FROM `looker-private-demo.retail.transaction_detail`  AS transactions
      LEFT JOIN UNNEST((
          transactions.line_items
      )) as transactions__line_items
      LEFT JOIN `looker-private-demo.retail.products`  AS products ON products.ID = transactions__line_items.product_id
      LEFT JOIN `looker-private-demo.retail.us_stores` AS stores ON stores.ID = transactions.store_id
      LEFT JOIN `looker-private-demo.retail.channels`  AS channels ON channels.ID = transactions.channel_id
      WHERE channels.NAME in ('In-store Self-checkout','In-store Tills') AND ((transactions.transaction_timestamp  < (TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', TIMESTAMP('2020-03-14 00:00:00')), 'America/Los_Angeles'))))

      UNION ALL

      SELECT
        'Online' as purchase_channel,
        'Delivery' as fulfillment_channel,
        (order_items.sale_price - inventory_items.cost) * 1.1  AS gross_magin,
        order_items.sale_price  AS sale_price,
        order_items.created_at as transaction_date,
        order_items.delivered_at as delivery_date,
        order_items.shipped_at as shipped_date,
        order_items.returned_at as returned_date,
        order_items.order_id  AS transaction_id,
        null as store_name,
        null as store_latitude,
        null as store_longitude,
        null AS store_state,
        null AS store_sq_ft,
        TRIM(products.category)  AS product_category,
        TRIM(products.brand)  AS products_brand,
        CASE
            WHEN products.CATEGORY IN ('Accessories', 'Swim', 'Socks', 'Socks & Hosiery', 'Leggings', 'Plus', 'Sleep & Lounge') THEN 'Accessories'
            WHEN products.CATEGORY IN ('Jeans', 'Tops & Tees', 'Shorts', 'Sweaters', 'Underwear', 'Intimates', 'Jumpsuits & Rompers', 'Maternity') THEN 'Casual Wear'
            WHEN products.CATEGORY IN ('Dresses', 'Skirts', 'Blazers & Jackets', 'Pants', 'Pants & Capris', 'Suits') THEN 'Formal Wear'
            WHEN products.CATEGORY IN ('Clothing Sets', 'Suits & Sport Coats', 'Outerwear & Coats', 'Fashion Hoodies & Sweatshirts', 'Suits', 'Active') THEN 'Outerwear'
            ELSE 'Other'
        END AS product_area,
        TRIM(products.name)  AS product_name,
        products.sku  AS product_sku,
        TRIM(products.department)  AS products_department
      FROM looker-private-demo.ecomm.order_items  AS order_items
      FULL OUTER JOIN looker-private-demo.ecomm.inventory_items  AS inventory_items ON inventory_items.id = order_items.inventory_item_id
      LEFT JOIN looker-private-demo.ecomm.users  AS users ON order_items.user_id = users.id
      LEFT JOIN looker-private-demo.ecomm.products  AS products ON products.id = inventory_items.product_id
      WHERE users.country = 'USA'

      UNION ALL

      SELECT
        'Online' as purchase_channel,
        'Delivery' as fulfillment_channel,
        (order_items.sale_price - inventory_items.cost) * 1.1  AS gross_magin,
        order_items.sale_price  AS sale_price,
        order_items.created_at as transaction_date,
        order_items.delivered_at as delivery_date,
        order_items.shipped_at as shipped_date,
        order_items.returned_at as returned_date,
        order_items.order_id  AS transaction_id,
        null as store_name,
        null as store_latitude,
        null as store_longitude,
        null AS store_state,
        null AS store_sq_ft,
        TRIM(products.category)  AS product_category,
        TRIM(products.brand)  AS products_brand,
        CASE
            WHEN products.CATEGORY IN ('Accessories', 'Swim', 'Socks', 'Socks & Hosiery', 'Leggings', 'Plus', 'Sleep & Lounge') THEN 'Accessories'
            WHEN products.CATEGORY IN ('Jeans', 'Tops & Tees', 'Shorts', 'Sweaters', 'Underwear', 'Intimates', 'Jumpsuits & Rompers', 'Maternity') THEN 'Casual Wear'
            WHEN products.CATEGORY IN ('Dresses', 'Skirts', 'Blazers & Jackets', 'Pants', 'Pants & Capris', 'Suits') THEN 'Formal Wear'
            WHEN products.CATEGORY IN ('Clothing Sets', 'Suits & Sport Coats', 'Outerwear & Coats', 'Fashion Hoodies & Sweatshirts', 'Suits', 'Active') THEN 'Outerwear'
            ELSE 'Other'
        END AS product_area,
        TRIM(products.name)  AS product_name,
        products.sku  AS product_sku,
        TRIM(products.department)  AS products_department
      FROM looker-private-demo.ecomm.order_items  AS order_items
      FULL OUTER JOIN looker-private-demo.ecomm.inventory_items  AS inventory_items ON inventory_items.id = order_items.inventory_item_id
      LEFT JOIN looker-private-demo.ecomm.users  AS users ON order_items.user_id = users.id
      LEFT JOIN looker-private-demo.ecomm.products  AS products ON products.id = inventory_items.product_id
      WHERE
        (order_items.created_at  >= TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', TIMESTAMP('2020-03-13 00:00:00')), 'America/Los_Angeles')) AND users.country = 'USA'
      )
      GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13
      )
      WHERE (customer_id <= 65000 and purchase_channel = 'In-store') OR (customer_id >= 60000 and fulfillment_channel = 'Delivery') OR (customer_id >= 45000 and customer_id <= 80000 and fulfillment_channel = 'In-store Pickup')
       ;;
  }

  dimension: reporting_period {
    type: string
    sql: CASE
        WHEN EXTRACT(YEAR from ${transaction_raw}) = EXTRACT(YEAR from CURRENT_TIMESTAMP())
        AND ${transaction_raw} < CURRENT_TIMESTAMP()
        THEN 'This Year to Date'

        WHEN EXTRACT(YEAR from ${transaction_raw}) + 1 = EXTRACT(YEAR from CURRENT_TIMESTAMP())
        AND CAST(FORMAT_TIMESTAMP('%j', ${transaction_raw}) AS INT64) <= CAST(FORMAT_TIMESTAMP('%j', CURRENT_TIMESTAMP()) AS INT64)
        THEN 'Last Year to Date'

      END
       ;;
  }

  measure: customer_count {
    type: count_distinct
    sql: ${customer_id} ;;
  }

  measure: first_purchase {
    type: string
    sql: min(${transaction_date}) ;;
  }

  measure: last_purchase {
    type: string
    sql: max(${transaction_date}) ;;
  }

  measure: transaction_count {
    type: count
  }

  measure: l30_transaction_count {
    type: count
    filters: [last_30: "Yes"]
  }

  measure: l90_transaction_count {
    type: count
    filters: [last_90: "Yes"]
  }

  measure: l180_transaction_count {
    type: count
    filters: [last_180: "Yes"]
  }

  measure: l360_transaction_count {
    type: count
    filters: [last_360: "Yes"]
  }

  measure: return_count {
    type: count
    filters: [is_returned: "Yes"]
  }

  measure: discounted_transaction_count {
    type: count
    filters: [is_discounted: "Yes"]
  }

  measure: online_transaction_count {
    filters: [purchase_channel: "Online"]
    type: count
  }

  measure: curbside_transaction_count {
    type: count
    filters: [fulfillment_channel: "In-store Pickup"]
  }

  measure: instore_transaction_count {
    filters: [purchase_channel: "In-store"]
    type: count
  }

  dimension: is_discounted {
    type: yesno
    sql: ${offer_type} is not null ;;
  }

  dimension: is_returned {
    type: yesno
    sql: ${returned_raw} is not null ;;
  }

  dimension: last_30 {
    type: yesno
    sql: ${transaction_raw} >= ((TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', TIMESTAMP_ADD(TIMESTAMP_TRUNC(TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', CURRENT_TIMESTAMP(), 'America/Los_Angeles')), DAY), INTERVAL -29 DAY)), 'America/Los_Angeles'))) AND ${transaction_raw} < ((TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', TIMESTAMP_ADD(TIMESTAMP_ADD(TIMESTAMP_TRUNC(TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', CURRENT_TIMESTAMP(), 'America/Los_Angeles')), DAY), INTERVAL -29 DAY), INTERVAL 30 DAY)), 'America/Los_Angeles'))) ;;
  }

  dimension: last_90 {
    type: yesno
    sql: ${transaction_raw} >= ((TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', TIMESTAMP_ADD(TIMESTAMP_TRUNC(TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', CURRENT_TIMESTAMP(), 'America/Los_Angeles')), DAY), INTERVAL -89 DAY)), 'America/Los_Angeles'))) AND ${transaction_raw} < ((TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', TIMESTAMP_ADD(TIMESTAMP_ADD(TIMESTAMP_TRUNC(TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', CURRENT_TIMESTAMP(), 'America/Los_Angeles')), DAY), INTERVAL -89 DAY), INTERVAL 90 DAY)), 'America/Los_Angeles'))) ;;
  }

  dimension: last_180 {
    type: yesno
    sql: ${transaction_raw} >= ((TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', TIMESTAMP_ADD(TIMESTAMP_TRUNC(TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', CURRENT_TIMESTAMP(), 'America/Los_Angeles')), DAY), INTERVAL -179 DAY)), 'America/Los_Angeles'))) AND ${transaction_raw} < ((TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', TIMESTAMP_ADD(TIMESTAMP_ADD(TIMESTAMP_TRUNC(TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', CURRENT_TIMESTAMP(), 'America/Los_Angeles')), DAY), INTERVAL -179 DAY), INTERVAL 180 DAY)), 'America/Los_Angeles'))) ;;
  }

  dimension: last_360 {
    type: yesno
    sql: ${transaction_raw} >= ((TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', TIMESTAMP_ADD(TIMESTAMP_TRUNC(TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', CURRENT_TIMESTAMP(), 'America/Los_Angeles')), DAY), INTERVAL -359 DAY)), 'America/Los_Angeles'))) AND ${transaction_raw} < ((TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', TIMESTAMP_ADD(TIMESTAMP_ADD(TIMESTAMP_TRUNC(TIMESTAMP(FORMAT_TIMESTAMP('%F %H:%M:%E*S', CURRENT_TIMESTAMP(), 'America/Los_Angeles')), DAY), INTERVAL -359 DAY), INTERVAL 360 DAY)), 'America/Los_Angeles'))) ;;
  }

  dimension: customer_id {
    value_format_name: id
    type: number
    sql: ${TABLE}.customer_id ;;
  }

  dimension_group: delivered {
    type: time
    timeframes: [
      raw,
      date,
      week,
      month,
      quarter,
      year
    ]
    convert_tz: no
    datatype: date
    sql: ${TABLE}.delivered_date ;;
  }

  dimension: fulfillment_channel {
    type: string
    sql: ${TABLE}.fulfillment_channel ;;
  }

  dimension: offer_type {
    type: string
    sql: COALESCE(${TABLE}.offer_type,'None') ;;
  }

  dimension: purchase_channel {
    type: string
    sql: ${TABLE}.purchase_channel ;;
  }

  dimension_group: returned {
    type: time
    timeframes: [
      raw,
      time,
      date,
      week,
      month,
      quarter,
      year
    ]
    sql: ${TABLE}.returned_date ;;
  }

  dimension_group: shipped {
    type: time
    timeframes: [
      raw,
      date,
      week,
      month,
      quarter,
      year
    ]
    convert_tz: no
    datatype: date
    sql: ${TABLE}.shipped_date ;;
  }

  dimension: store_latitude {
    type: number
    sql: ${TABLE}.store_latitude ;;
  }

  dimension: store_longitude {
    type: number
    sql: ${TABLE}.store_longitude ;;
  }

  dimension: store_name {
    type: string
    sql: ${TABLE}.store_name ;;
  }

  dimension: store_sq_ft {
    type: number
    sql: ${TABLE}.Store_sq_ft ;;
  }

  dimension: store_state {
    type: string
    sql: ${TABLE}.store_state ;;
  }

  dimension_group: transaction {
    type: time
    timeframes: [
      raw,
      time,
      date,
      week,
      month,
      month_name,
      quarter,
      year
    ]
    sql: ${TABLE}.transaction_date ;;
  }

  dimension: transaction_details {
    hidden: yes
    sql: ${TABLE}.transaction_details ;;
  }

  dimension: transaction_id {
    primary_key: yes
    type: number
    sql: ${TABLE}.transaction_id ;;
  }
}

view: omni_channel_transactions__transaction_details {
  dimension: gross_margin {
    type: number
    sql: ${TABLE}.gross_margin ;;
  }

  dimension: product_area {
    type: string
    sql: ${TABLE}.product_area ;;
  }

  dimension: product_brand {
    type: string
    sql: ${TABLE}.product_brand ;;
  }

  dimension: product_category {
    bypass_suggest_restrictions: yes
    suggestable: yes
    full_suggestions: yes
    type: string
    sql: ${TABLE}.product_category ;;
  }

  dimension: product_department {
    type: string
    sql: ${TABLE}.product_department ;;
  }

  dimension: product_name {
    type: string
    sql: ${TABLE}.product_name ;;
  }

  dimension: product_sku {
    primary_key: yes
    type: string
    sql: ${TABLE}.product_sku ;;
  }

  dimension: sale_price {
    value_format:"[>=1000000]$0.0,,\"M\";[>=1000]$0.0,\"K\";$0.0"
    type: number
    sql: ${TABLE}.sale_price ;;
  }

  measure: total_profit {
    value_format:"[>=1000000]$0.0,,\"M\";[>=1000]$0.0,\"K\";$0.0"
    type: sum
    sql: ${gross_margin} ;;
  }

  measure: total_sales {
    value_format:"[>=1000000]$0.0,,\"M\";[>=1000]$0.0,\"K\";$0.0"
    type: sum
    sql: ${sale_price} ;;
  }

  measure: profit_margin {
    type: number
    sql: ${total_profit} / nullif(${total_sales},0) ;;
    value_format_name: percent_2
  }

  measure: recommended_products {
    type: list
    list_field: product_name
  }

  measure: item_count {
    type: count
  }
}
