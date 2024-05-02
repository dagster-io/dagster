view: products {
  label: "Products 📦"
  sql_table_name: `looker-private-demo.retail.products` ;;
  drill_fields: [id]

  dimension: id {
    primary_key: yes
    type: number
    hidden: yes
    sql: ${TABLE}.ID ;;
  }

  dimension: brand {
    type: string
    sql: ${TABLE}.BRAND ;;
    drill_fields: [name]
  }

  dimension: category {
    type: string
    sql: ${TABLE}.CATEGORY ;;
    drill_fields: [stores.name,brand]
    link: {
      label: "{{value}} Item Dynamics"
      icon_url: "https://i.imgur.com/W4tVGrj.png"
      url: "/dashboards/TSGWx3mvSYoyNKLKLDssXW?Focus%20Category={{value | encode_uri}}&Minimum%20Purchase%20Frequency="
    }
    action: {
      label: "Text/Call {{rendered_value}} Category Manager"
      icon_url: "https://cdn.iconscout.com/icon/free/png-256/twilio-282195.png"
      url: "https://retail-demo-app-idhn2cvrpq-uc.a.run.app/api/contactCategoryManager?category={{value | encode_uri}}"
      param: {
        name: "category"
        value: "{{value | encode_uri}}"
      }
      form_param: {
        name: "message"
        type: textarea
        label: "Message"
        required: yes
        default: "Hi, can you please check out what's going on in {{rendered_value}}? /dashboards/Ipxk660N88jaUxsHolxRts?Category={{value | encode_uri}}"
      }
    }
  }

  dimension: department {
    label: "Target Gender"
    type: string
    sql: ${TABLE}.DEPARTMENT ;;
  }

  dimension: name {
    label: "Product Name"
    type: string
    sql: ${TABLE}.NAME ;;
    link: {
      label: "Drive attachments for {{rendered_value}}"
      icon_url: "https://i.imgur.com/W4tVGrj.png"
      url: "/dashboards/TSGWx3mvSYoyNKLKLDssXW?Focus%20Product={{value | encode_uri}}&Minimum%20Purchase%20Frequency="
    }
  }

  dimension: sku {
    type: string
    sql: ${TABLE}.SKU ;;
  }

  dimension: area {
    type: string
    sql: CASE
      WHEN ${category} IN ('Accessories', 'Swim', 'Socks', 'Socks & Hosiery', 'Leggings', 'Plus', 'Sleep & Lounge') THEN 'Accessories'
      WHEN ${category} IN ('Jeans', 'Tops & Tees', 'Shorts', 'Sweaters', 'Underwear', 'Intimates', 'Jumpsuits & Rompers', 'Maternity') THEN 'Casual Wear'
      WHEN ${category} IN ('Dresses', 'Skirts', 'Blazers & Jackets', 'Pants', 'Pants & Capris', 'Suits') THEN 'Formal Wear'
      WHEN ${category} IN ('Clothing Sets', 'Suits & Sport Coats', 'Outerwear & Coats', 'Fashion Hoodies & Sweatshirts', 'Suits', 'Active') THEN 'Outerwear'
    END;;
    drill_fields: [category]
  }

  ##### DERIVED DIMENSIONS #####

  dimension: product_image {
    type: string
    sql: ${name} ;;
    html: <img src="https://us-central1-looker-private-demo.cloudfunctions.net/imageSearch?q={{value | encode_uri }}" style="height: 50px; max-width: 150px;" /> ;;
  }

  ##### MEASURES #####

  measure: number_of_products {
    type: count_distinct
    sql: ${id} ;;
  }
}
