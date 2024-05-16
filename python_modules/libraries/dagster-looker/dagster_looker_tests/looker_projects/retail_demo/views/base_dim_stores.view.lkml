view: stores {
  label: "Stores 🏪"
#   sql_table_name: looker-private-demo.retail.us_stores ;;
  derived_table: {
    datagroup_trigger: monthly
    sql: SELECT * FROM `looker-private-demo.retail.us_stores` WHERE id IN (SELECT distinct store_id from ${transactions.SQL_TABLE_NAME});;
  }

  dimension: id {
    primary_key: yes
    type: number
    sql: ${TABLE}.ID ;;
  }

  dimension: latitude {
    type: number
    hidden: yes
    sql: ${TABLE}.LATITUDE ;;

  }

  dimension: longitude {
    type: number
    hidden: yes
    sql: ${TABLE}.LONGITUDE ;;
  }

  dimension: name {
    drill_fields: [products.category]
    label: "Store Name"
    type: string
    sql: ${TABLE}.NAME ;;
    link: {
      url: "/dashboards/EsHSwCce7zkZr7uz6X5kbO?Date={{ _filters['transactions.date_comparison_filter'] | encode_uri }}&Store={{value | encode_uri}}"
      label: "Drill down into {{rendered_value}}"
    }
    link: {
      url: "https://retail-demo-app-idhn2cvrpq-uc.a.run.app/api/contactStoreManager?store={{value | encode_uri}}"
      label: "Text/Call {{rendered_value}} Store Manager via Google App Engine"
      icon_url: "https://cdn.iconscout.com/icon/free/png-256/twilio-282195.png"
    }
#     action: {
#       label: "Text/Call {{rendered_value}} Store Manager"
#       icon_url: "https://cdn.iconscout.com/icon/free/png-256/twilio-282195.png"
#       url: "https://retail-demo-app-idhn2cvrpq-uc.a.run.app/api/contactStoreManager?store={{value | encode_uri}}"
#       param: {
#         name: "store"
#         value: "{{value | encode_uri}}"
#       }
#       form_param: {
#         name: "message"
#         type: textarea
#         label: "Message"
#         required: yes
#         default: "Hi, can you please check out what's going on in {{rendered_value}}? /dashboards/WQKf302aPo8IEFvc2EkSQP?Store={{value | encode_uri}}"
#       }
#     }
  }

  dimension: state {
    type: string
    group_label: "Store Info"
    sql: ${TABLE}.State ;;
  }

  dimension: sq_ft {
    type: string
    group_label: "Store Info"
    sql: ${TABLE}.sq_ft ;;
  }

  ##### DERIVED DIMENSIONS #####

  dimension: location {
    type: location
    group_label: "Store Info"
    sql_latitude: ${latitude} ;;
    sql_longitude: ${longitude} ;;
  }

  dimension: store_size_grouping {
    type: string
    sql: CASE
      WHEN ${sq_ft} <= 70000 THEN 'S'
      WHEN ${sq_ft} <= 100000 THEN 'M'
      WHEN ${sq_ft} <= 130000 THEN 'L'
      WHEN ${sq_ft} <= 160000 THEN 'XL'
    END ;;
    order_by_field: store_size_grouping_order
  }

  dimension: store_size_grouping_order {
    hidden: yes
    type: number
    sql: CASE ${store_size_grouping}
      WHEN 'S' THEN 1
      WHEN 'M' THEN 2
      WHEN 'L' THEN 3
      WHEN 'XL' THEN 4
    END
    ;;
  }

  filter: store_for_comparison {
    type: string
    group_label: "Store Comparison"
    suggest_dimension: stores.name
  }

  dimension: store_comparison_vs_stores_in_tier {
    type: string
    group_label: "Store Comparison"
    sql: CASE
      WHEN {% condition store_for_comparison %} ${name} {% endcondition %} THEN CONCAT('1- ',${name})
      ELSE ${name}
    END;;
  }

  dimension: store_comparison_vs_stores_in_tier_with_weather {
    type: string
    group_label: "Store Comparison"
    sql: CASE
      WHEN {% condition store_for_comparison %} ${name} {% endcondition %} THEN CONCAT('1- ',${name})
      ELSE ${name}
    END;;
    html: {{rendered_value}}{% if store_weather.average_daily_precipitation._value < 2.0 %} - 🌞{% elsif store_weather.average_daily_precipitation._value < 4.0 %} - ☁️{% elsif store_weather.average_daily_precipitation._value > 4.0 %} - 🌧️️{% else %}{% endif %};;
    action: {
      label: "Text/Call {{rendered_value}} Store Manager"
      icon_url: "https://cdn.iconscout.com/icon/free/png-256/twilio-282195.png"
      url: "https://retail-demo-app-idhn2cvrpq-uc.a.run.app/api/contactStoreManager?store={{value | encode_uri}}"
      param: {
        name: "store"
        value: "{{value | encode_uri}}"
      }
      form_param: {
        name: "message"
        type: textarea
        label: "Message"
        required: yes
        default: "Hi, can you please check out what's going on in {{rendered_value}}? /dashboards/WQKf302aPo8IEFvc2EkSQP?Store={{value | encode_uri}}"
      }
    }
  }

  dimension: store_comparison_vs_tier {
    type: string
    group_label: "Store Comparison"
    sql: CASE
      WHEN {% condition store_for_comparison %} ${name} {% endcondition %} THEN CONCAT('1- ',${name})
      ELSE '2- Rest of Stores in Tier'
    END;;
  }
}
