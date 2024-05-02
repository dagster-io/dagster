- dashboard: customer_segment_deepdive
  title: Customer Segment Deep-dive
  layout: newspaper
  elements:
  - title: Customer Coverage
    name: Customer Coverage
    model: retail_block_model
    explore: transactions
    type: looker_map
    fields: [customers.location, transactions__line_items.total_sales]
    filters:
      transactions.transaction_date: 12 months
      customers.country: USA
      customers.location_bin_level: '9'
      customers.location: inside box from 55.7765730186677, -157.50000000000003 to
        21.94304553343818, -45
    sorts: [transactions__line_items.total_sales desc]
    limit: 5000
    column_limit: 50
    map_plot_mode: automagic_heatmap
    heatmap_gridlines: false
    heatmap_gridlines_empty: false
    heatmap_opacity: 0.5
    show_region_field: true
    draw_map_labels_above_data: true
    map_tile_provider: dark
    map_position: custom
    map_latitude: 37.96152331396614
    map_longitude: -96.7236328125
    map_zoom: 4
    map_scale_indicator: 'off'
    map_pannable: true
    map_zoomable: true
    map_marker_type: circle
    map_marker_icon_name: default
    map_marker_radius_mode: proportional_value
    map_marker_units: meters
    map_marker_proportional_scale_type: linear
    map_marker_color_mode: fixed
    show_view_names: false
    show_legend: true
    quantize_map_value_colors: false
    reverse_map_value_colors: false
    listen:
      Customer Segment: customer_clustering_prediction.customer_segment
    row: 2
    col: 0
    width: 12
    height: 8
  - title: Sales
    name: Sales
    model: retail_block_model
    explore: transactions
    type: single_value
    fields: [transactions.selected_comparison, transactions__line_items.total_sales,
      transactions.number_of_transactions, transactions__line_items.average_basket_size,
      transactions__line_items.total_quantity]
    filters:
      transactions.transaction_date: 2 years
      transactions.comparison_type: year
      transactions.selected_comparison: "-NULL"
    sorts: [transactions.selected_comparison desc]
    limit: 500
    column_limit: 50
    dynamic_fields: [{table_calculation: vs_ly, label: vs LY, expression: "${transactions__line_items.total_sales}/offset(${transactions__line_items.total_sales},1)-1",
        value_format: !!null '', value_format_name: percent_1, _kind_hint: measure,
        _type_hint: number}]
    custom_color_enabled: true
    custom_color: "#5A30C2"
    show_single_value_title: true
    show_comparison: true
    comparison_type: change
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    series_types: {}
    hidden_fields: [transactions__line_items.average_basket_size, transactions__line_items.total_quantity,
      transactions.number_of_transactions]
    listen:
      Customer Segment: customer_clustering_prediction.customer_segment
      Date Range: transactions.date_comparison_filter
    row: 2
    col: 12
    width: 6
    height: 4
  - title: Transactions
    name: Transactions
    model: retail_block_model
    explore: transactions
    type: single_value
    fields: [transactions.selected_comparison, transactions__line_items.total_sales,
      transactions.number_of_transactions, transactions__line_items.average_basket_size,
      transactions__line_items.total_quantity]
    filters:
      transactions.transaction_date: 2 years
      transactions.comparison_type: year
      transactions.selected_comparison: "-NULL"
    sorts: [transactions.selected_comparison desc]
    limit: 500
    column_limit: 50
    dynamic_fields: [{table_calculation: vs_ly, label: vs LY, expression: "${transactions.number_of_transactions}/offset(${transactions.number_of_transactions},1)-1",
        value_format: !!null '', value_format_name: percent_1, _kind_hint: measure,
        _type_hint: number}]
    custom_color_enabled: true
    custom_color: "#5A30C2"
    show_single_value_title: true
    show_comparison: true
    comparison_type: change
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    series_types: {}
    hidden_fields: [transactions__line_items.average_basket_size, transactions__line_items.total_sales,
      transactions__line_items.total_quantity]
    listen:
      Customer Segment: customer_clustering_prediction.customer_segment
      Date Range: transactions.date_comparison_filter
    row: 2
    col: 18
    width: 6
    height: 4
  - title: Basket Size
    name: Basket Size
    model: retail_block_model
    explore: transactions
    type: single_value
    fields: [transactions.selected_comparison, transactions__line_items.total_sales,
      transactions.number_of_transactions, transactions__line_items.average_basket_size,
      transactions__line_items.total_quantity]
    filters:
      transactions.transaction_date: 2 years
      transactions.comparison_type: year
      transactions.selected_comparison: "-NULL"
    sorts: [transactions.selected_comparison desc]
    limit: 500
    column_limit: 50
    dynamic_fields: [{table_calculation: vs_ly, label: vs LY, expression: "${transactions__line_items.average_basket_size}/offset(${transactions__line_items.average_basket_size},1)-1",
        value_format: !!null '', value_format_name: percent_1, _kind_hint: measure,
        _type_hint: number}]
    custom_color_enabled: true
    custom_color: "#5A30C2"
    show_single_value_title: true
    show_comparison: true
    comparison_type: change
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    series_types: {}
    hidden_fields: [transactions__line_items.total_sales, transactions__line_items.total_quantity,
      transactions.number_of_transactions]
    listen:
      Customer Segment: customer_clustering_prediction.customer_segment
      Date Range: transactions.date_comparison_filter
    row: 6
    col: 12
    width: 6
    height: 4
  - title: Quantity
    name: Quantity
    model: retail_block_model
    explore: transactions
    type: single_value
    fields: [transactions.selected_comparison, transactions__line_items.total_sales,
      transactions.number_of_transactions, transactions__line_items.average_basket_size,
      transactions__line_items.total_quantity]
    filters:
      transactions.transaction_date: 2 years
      transactions.comparison_type: year
      transactions.selected_comparison: "-NULL"
    sorts: [transactions.selected_comparison desc]
    limit: 500
    column_limit: 50
    dynamic_fields: [{table_calculation: vs_ly, label: vs LY, expression: "${transactions__line_items.total_quantity}/offset(${transactions__line_items.total_quantity},1)-1",
        value_format: !!null '', value_format_name: percent_1, _kind_hint: measure,
        _type_hint: number}]
    custom_color_enabled: true
    custom_color: "#5A30C2"
    show_single_value_title: true
    show_comparison: true
    comparison_type: change
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    series_types: {}
    hidden_fields: [transactions__line_items.total_sales, transactions.number_of_transactions,
      transactions__line_items.average_basket_size]
    listen:
      Customer Segment: customer_clustering_prediction.customer_segment
      Date Range: transactions.date_comparison_filter
    row: 6
    col: 18
    width: 6
    height: 4
  - title: Customer Segment
    name: Customer Segment
    model: retail_block_model
    explore: transactions
    type: single_value
    fields: [customer_clustering_prediction.customer_segment]
    filters:
      transactions.transaction_date: 30 days
    sorts: [customer_clustering_prediction.customer_segment]
    limit: 500
    column_limit: 50
    series_types: {}
    listen:
      Customer Segment: customer_clustering_prediction.customer_segment
    row: 0
    col: 0
    width: 24
    height: 2
  - name: ''
    type: text
    title_text: ''
    subtitle_text: ''
    body_text: |-
      <div align="center">
      <div><img src="https://upload.wikimedia.org/wikipedia/en/thumb/8/83/Salesforce_logo.svg/1200px-Salesforce_logo.svg.png" height="150"></div>
      <div><a href="https://retail-demo-app-idhn2cvrpq-uc.a.run.app/api/exportToSalesforce" target="_blank"><button style="color:white; padding: 10px 20px; background-color: #0088bd; border: none; font-size: 16px;">Create campaign segment</button></a></div>
      </div>
    row: 12
    col: 18
    width: 6
    height: 6
  - title: Potential Value from 10% Reactivation
    name: Potential Value from 10% Reactivation
    model: retail_block_model
    explore: transactions
    type: single_value
    fields: [transactions__line_items.total_sales]
    filters:
      transactions.transaction_date: 12 months
      customer_facts.customer_spend_trend_past_year: "<-0.1"
    limit: 5000
    column_limit: 50
    dynamic_fields: [{table_calculation: reactivation_threshold, label: Reactivation
          Threshold, expression: '0.1', value_format: !!null '', value_format_name: !!null '',
        _kind_hint: dimension, _type_hint: number}, {table_calculation: potential_value,
        label: Potential Value, expression: "${transactions__line_items.total_sales}*${reactivation_threshold}",
        value_format: !!null '', value_format_name: usd_0, _kind_hint: measure, _type_hint: number}]
    custom_color_enabled: true
    custom_color: "#49c244"
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    show_view_names: false
    show_row_numbers: true
    transpose: false
    truncate_text: true
    hide_totals: false
    hide_row_totals: false
    size_to_fit: true
    series_cell_visualizations:
      customer_facts.customer_spend_trend_past_year:
        is_active: true
        palette:
          palette_id: retailer-scheme-diverging-0
          collection_id: retailer-scheme
    table_theme: white
    limit_displayed_rows: false
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
    series_value_format:
      customer_facts.customer_id:
        name: id
        format_string: '0'
        label: ID
    map_plot_mode: automagic_heatmap
    heatmap_gridlines: false
    heatmap_gridlines_empty: false
    heatmap_opacity: 0.5
    show_region_field: true
    draw_map_labels_above_data: true
    map_tile_provider: dark
    map_position: custom
    map_latitude: 37.96152331396614
    map_longitude: -96.7236328125
    map_zoom: 4
    map_scale_indicator: 'off'
    map_pannable: true
    map_zoomable: true
    map_marker_type: circle
    map_marker_icon_name: default
    map_marker_radius_mode: proportional_value
    map_marker_units: meters
    map_marker_proportional_scale_type: linear
    map_marker_color_mode: fixed
    show_legend: true
    quantize_map_value_colors: false
    reverse_map_value_colors: false
    series_types: {}
    hidden_fields: [reactivation_threshold, transactions__line_items.total_sales]
    listen:
      Customer Segment: customer_clustering_prediction.customer_segment
    row: 10
    col: 18
    width: 6
    height: 2
  - name: " (2)"
    type: text
    title_text: ''
    subtitle_text: ''
    body_text: |-
      **Recommended Action ?**
      These are our previously loyal customers in our segment, who have dropped off over the past year. Click the button on the right to create a campaign segment in Salesforce to prepare an email campaign for the CRM manager.
    row: 10
    col: 0
    width: 3
    height: 8
  - title: Customers for Reactivation Campaign
    name: Customers for Reactivation Campaign
    model: retail_block_model
    explore: transactions
    type: looker_grid
    fields: [customer_facts.customer_id, customer_facts.customer_spend_trend_past_year,
      customers.email, customers.gender, customers.age, customers.postcode]
    filters:
      transactions.transaction_date: 12 months
      customer_facts.customer_spend_trend_past_year: "<-0.1"
    sorts: [customer_facts.customer_spend_trend_past_year]
    limit: 500
    query_timezone: America/Los_Angeles
    show_totals: true
    show_row_totals: true
    show_view_names: false
    show_row_numbers: true
    transpose: false
    truncate_text: true
    size_to_fit: true
    series_cell_visualizations:
      customer_facts.customer_spend_trend_past_year:
        is_active: true
        palette:
          palette_id: 50d44102-be13-bd23-eed2-8000589f3610
          collection_id: f14810d2-98d7-42df-82d0-bc185a074e42
          custom_colors:
          - "#ab2824"
          - "#ffffff"
    table_theme: white
    limit_displayed_rows: false
    enable_conditional_formatting: false
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    series_types: {}
    listen:
      Customer Segment: customer_clustering_prediction.customer_segment
    row: 10
    col: 3
    width: 15
    height: 8
  filters:
  - name: Customer Segment
    title: Customer Segment
    type: field_filter
    default_value: Emerging Millennials 🥑
    allow_multiple_values: false
    required: true
    model: retail_block_model
    explore: transactions
    listens_to_filters: []
    field: customer_clustering_prediction.customer_segment
  - name: Date Range
    title: Date Range
    type: date_filter
    default_value: 30 days
    allow_multiple_values: true
    required: false
