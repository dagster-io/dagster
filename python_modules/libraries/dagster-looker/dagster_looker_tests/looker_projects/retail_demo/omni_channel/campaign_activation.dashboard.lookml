- dashboard: campaign_activation
  title: Campaign Activation
  layout: newspaper
  preferred_viewer: dashboards-next
  elements:
  - title: Predicted High CLV Customers
    name: Predicted High CLV Customers
    model: omni_channel
    explore: omni_channel_transactions
    type: looker_grid
    fields: [c360.customer_id, customers.name, customers.email, customers.address,
      c360.predicted_clv, recommended_products, c360.risk_of_churn]
    sorts: [c360.predicted_clv desc]
    limit: 100
    dynamic_fields: [{measure: recommended_products, based_on: omni_channel_transactions__transaction_details.product_name,
        type: list, label: Recommended Products, expression: !!null '', value_format: !!null '',
        value_format_name: !!null '', _kind_hint: measure, _type_hint: list}]
    query_timezone: America/Los_Angeles
    show_view_names: false
    show_row_numbers: false
    transpose: false
    truncate_text: false
    hide_totals: false
    hide_row_totals: false
    size_to_fit: true
    table_theme: white
    limit_displayed_rows: false
    enable_conditional_formatting: true
    header_text_alignment: left
    header_font_size: '15'
    rows_font_size: '13'
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    show_sql_query_menu_options: false
    show_totals: true
    show_row_totals: true
    series_column_widths:
      c360.customer_id: 130
      customers.name: 175
      c360.risk_of_churn: 133
      c360.predicted_clv: 300
    series_cell_visualizations:
      recommended_products:
        is_active: true
      c360.predicted_clv:
        is_active: true
        value_display: true
    series_text_format:
      c360.risk_of_churn:
        align: left
    conditional_formatting: [{type: along a scale..., value: !!null '', background_color: "#4285F4",
        font_color: !!null '', color_application: {collection_id: google, palette_id: google-diverging-0,
          options: {steps: 5, constraints: {min: {type: minimum}, mid: {type: number,
                value: 0}, max: {type: maximum}}, mirror: false, reverse: true, stepped: false}},
        bold: false, italic: false, strikethrough: false, fields: [c360.risk_of_churn]}]
    defaults_version: 1
    listen:
      Customer Type: c360.customer_type
      Has Visited Website?: c360.has_visited_website
      Likely to Interact With: c360.acquisition_source
      Likely to Purchase: omni_channel_transactions__transaction_details.product_category
      Likely to Respond To: omni_channel_transactions.offer_type
      Churn Risk: c360.risk_of_churn_100
      Lifetime Purchases: c360.transaction_count
    row: 0
    col: 0
    width: 20
    height: 14
  - name: ''
    type: text
    title_text: ''
    subtitle_text: ''
    body_text: "<a style=\"\n\tcolor: #fff;\n    width: 98%;\n    background-color:\
      \ #ed750a;\n    border-color: #ed750a;\n    float: left;\n    font-weight: 400;\n\
      \    text-align: center;\n    vertical-align: middle;\n    cursor: pointer;\n\
      \    user-select: none;\n    padding: 10px;\n    margin: 5px;\n    font-size:\
      \ 1rem;\n    line-height: 1.5;\n    border-radius: 5px;\"\n    href=\"#\">\n\
      \    Send to Google Analytics\n</a>"
    row: 4
    col: 20
    width: 4
    height: 2
  - name: " (2)"
    type: text
    title_text: ''
    subtitle_text: ''
    body_text: "<a style=\"\n\tcolor: #fff;\nwidth: 98%;\n    background-color: #4B0082\t\
      ;\n    border-color: #4B0082\t;\n    float: left;\n    font-weight: 400;\n \
      \   text-align: center;\n    vertical-align: middle;\n    cursor: pointer;\n\
      \    user-select: none;\n    padding: 10px;\n    margin: 5px;\n    font-size:\
      \ 1rem;\n    line-height: 1.5;\n    border-radius: 5px;\"\n    href=\"#\">\n\
      \    Send to Marketo\n</a>"
    row: 2
    col: 20
    width: 4
    height: 2
  - name: " (3)"
    type: text
    title_text: ''
    subtitle_text: ''
    body_text: "<a style=\"\n\tcolor: #fff;\nwidth: 98%;\n    background-color: #294661;\n\
      \    border-color: #294661;\n    float: left;\n    font-weight: 400;\n    text-align:\
      \ center;\n    vertical-align: middle;\n    cursor: pointer;\n    user-select:\
      \ none;\n    padding: 10px;\n    margin: 5px;\n    font-size: 1rem;\n    line-height:\
      \ 1.5;\n    border-radius: 5px;\"\n    href=\"#\">\n    Send to SendGrid\n</a>"
    row: 0
    col: 20
    width: 4
    height: 2
  - name: " (4)"
    type: text
    title_text: ''
    subtitle_text: ''
    body_text: "<a style=\"\n\tcolor: #fff;\nwidth: 98%;\n    background-color: #1798c1;\n\
      \    border-color: #1798c1;\n    float: left;\n    font-weight: 400;\n    text-align:\
      \ center;\n    vertical-align: middle;\n    cursor: pointer;\n    user-select:\
      \ none;\n    padding: 10px;\n    margin: 5px;\n    font-size: 1rem;\n    line-height:\
      \ 1.5;\n    border-radius: 5px;\"\n    href=\"#\">\n    Send to Salesforce\n\
      </a>"
    row: 6
    col: 20
    width: 4
    height: 2
  filters:
  - name: Customer Type
    title: Customer Type
    type: field_filter
    default_value: Instore Only
    allow_multiple_values: true
    required: false
    ui_config:
      type: tag_list
      display: popover
    model: omni_channel
    explore: omni_channel_transactions
    listens_to_filters: []
    field: c360.customer_type
  - name: Has Visited Website?
    title: Has Visited Website?
    type: field_filter
    default_value: 'Yes'
    allow_multiple_values: true
    required: false
    ui_config:
      type: button_toggles
      display: inline
    model: omni_channel
    explore: omni_channel_transactions
    listens_to_filters: []
    field: c360.has_visited_website
  - name: Likely to Interact With
    title: Likely to Interact With
    type: field_filter
    default_value: ''
    allow_multiple_values: true
    required: false
    ui_config:
      type: tag_list
      display: popover
    model: omni_channel
    explore: omni_channel_transactions
    listens_to_filters: []
    field: c360.acquisition_source
  - name: Likely to Purchase
    title: Likely to Purchase
    type: field_filter
    default_value: ''
    allow_multiple_values: true
    required: false
    ui_config:
      type: tag_list
      display: popover
    model: omni_channel
    explore: omni_channel_transactions
    listens_to_filters: []
    field: omni_channel_transactions__transaction_details.product_category
  - name: Likely to Respond To
    title: Likely to Respond To
    type: field_filter
    default_value: ''
    allow_multiple_values: true
    required: false
    ui_config:
      type: tag_list
      display: popover
    model: omni_channel
    explore: omni_channel_transactions
    listens_to_filters: []
    field: omni_channel_transactions.offer_type
  - name: Churn Risk
    title: Churn Risk
    type: field_filter
    default_value: "[50,100]"
    allow_multiple_values: true
    required: false
    ui_config:
      type: range_slider
      display: inline
      options:
        min: 0
        max: 100
    model: omni_channel
    explore: omni_channel_transactions
    listens_to_filters: []
    field: c360.risk_of_churn_100
  - name: Lifetime Purchases
    title: Lifetime Purchases
    type: field_filter
    default_value: "[3,10]"
    allow_multiple_values: true
    required: false
    ui_config:
      type: range_slider
      display: inline
      options:
        min: 0
        max: 10
    model: omni_channel
    explore: omni_channel_transactions
    listens_to_filters: []
    field: c360.transaction_count
