- dashboard: customer_360
  title: Customer 360
  layout: newspaper
  preferred_viewer: dashboards-next
  elements:
  - title: Transaction Count by Channel
    name: Transaction Count by Channel
    model: omni_channel
    explore: omni_channel_transactions
    type: looker_area
    fields: [omni_channel_transactions.transaction_month, omni_channel_transactions.transaction_count,
      omni_channel_transactions.fulfillment_channel]
    pivots: [omni_channel_transactions.fulfillment_channel]
    filters:
      omni_channel_transactions.transaction_date: 12 months ago for 12 months
    sorts: [omni_channel_transactions.transaction_month desc, omni_channel_transactions.fulfillment_channel]
    limit: 500
    column_limit: 50
    row_total: right
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: false
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: normal
    limit_displayed_rows: false
    legend_position: center
    point_style: circle
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    show_null_points: false
    interpolation: monotone
    show_totals_labels: true
    show_silhouette: false
    totals_color: "#808080"
    y_axes: [{label: '', orientation: left, series: [{axisId: Assisted Checkout -
              omni_channel_transactions.transaction_count, id: Assisted Checkout -
              omni_channel_transactions.transaction_count, name: Assisted Checkout},
          {axisId: Delivery - omni_channel_transactions.transaction_count, id: Delivery
              - omni_channel_transactions.transaction_count, name: Delivery}, {axisId: In-store
              Pickup - omni_channel_transactions.transaction_count, id: In-store Pickup
              - omni_channel_transactions.transaction_count, name: In-store Pickup},
          {axisId: Self Checkout - omni_channel_transactions.transaction_count, id: Self
              Checkout - omni_channel_transactions.transaction_count, name: Self Checkout}],
        showLabels: false, showValues: true, unpinAxis: false, tickDensity: default,
        tickDensityCustom: 5, type: linear}]
    series_types: {}
    defaults_version: 1
    listen: {}
    row: 5
    col: 0
    width: 12
    height: 9
  - title: In-Store and Online
    name: In-Store and Online
    model: omni_channel
    explore: omni_channel_transactions
    type: single_value
    fields: [c360.customer_count]
    filters:
      c360.customer_type: Both Online and Instore
    limit: 500
    column_limit: 50
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    defaults_version: 1
    listen: {}
    row: 2
    col: 8
    width: 4
    height: 3
  - name: Customer Health
    type: text
    title_text: Customer Health
    subtitle_text: ''
    body_text: ''
    row: 43
    col: 0
    width: 24
    height: 2
  - name: Customer Acquisition
    type: text
    title_text: Customer Acquisition
    subtitle_text: ''
    body_text: ''
    row: 25
    col: 0
    width: 24
    height: 2
  - name: Omni-Channel Overview
    type: text
    title_text: Omni-Channel Overview
    subtitle_text: ''
    body_text: ''
    row: 0
    col: 0
    width: 24
    height: 2
  - name: Channel Analysis
    type: text
    title_text: Channel Analysis
    subtitle_text: ''
    body_text: ''
    row: 14
    col: 0
    width: 24
    height: 2
  - title: RFV
    name: RFV
    model: omni_channel
    explore: omni_channel_transactions
    type: treemap
    fields: [c360.customer_count, c360.rfm_rating]
    sorts: [c360.customer_count desc]
    limit: 500
    column_limit: 50
    hidden_fields: []
    hidden_points_if_no: []
    series_labels: {}
    show_view_names: false
    color_range: ["#4285F4", "#EA4335", "#FBBC04", "#34A853", "#5F6368", "#185ABC",
      "#9AA0A6", "#B31412", "#BDC1C6", "#EA8600", "#E8EAED", "#137333"]
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: none
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    defaults_version: 0
    series_types: {}
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    row: 45
    col: 0
    width: 12
    height: 9
  - title: Recency
    name: Recency
    model: omni_channel
    explore: omni_channel_transactions
    type: single_value
    fields: [c360.high_recency_customers, c360.customer_count, c360.low_recency_customers,
      c360.high_frequency_customers, c360.low_frequency_customers, c360.high_monetary_value_customers,
      c360.low_monetary_value_customers]
    limit: 500
    column_limit: 50
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: true
    comparison_type: progress_percentage
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    single_value_title: High Recency Customers
    comparison_label: Customers
    hidden_fields: []
    hidden_points_if_no: []
    series_labels: {}
    show_view_names: false
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: none
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    defaults_version: 1
    series_types: {}
    show_null_points: true
    interpolation: linear
    listen: {}
    row: 45
    col: 12
    width: 12
    height: 3
  - title: Frequency
    name: Frequency
    model: omni_channel
    explore: omni_channel_transactions
    type: single_value
    fields: [c360.high_recency_customers, c360.low_recency_customers, c360.high_frequency_customers,
      c360.customer_count, c360.low_frequency_customers, c360.high_monetary_value_customers,
      c360.low_monetary_value_customers]
    limit: 500
    column_limit: 50
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: true
    comparison_type: progress_percentage
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    single_value_title: High Frequency Customers
    comparison_label: Customers
    hidden_fields: [c360.high_recency_customers, c360.low_recency_customers]
    hidden_points_if_no: []
    series_labels: {}
    show_view_names: false
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: none
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    defaults_version: 1
    series_types: {}
    show_null_points: true
    interpolation: linear
    listen: {}
    row: 48
    col: 12
    width: 12
    height: 3
  - title: Value
    name: Value
    model: omni_channel
    explore: omni_channel_transactions
    type: single_value
    fields: [c360.high_recency_customers, c360.low_recency_customers, c360.high_frequency_customers,
      c360.low_frequency_customers, c360.high_monetary_value_customers, c360.customer_count,
      c360.low_monetary_value_customers]
    limit: 500
    column_limit: 50
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: true
    comparison_type: progress_percentage
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    single_value_title: High Value Customers
    comparison_label: Customers
    hidden_fields: [c360.high_recency_customers, c360.low_recency_customers, c360.high_frequency_customers,
      c360.low_frequency_customers]
    hidden_points_if_no: []
    series_labels: {}
    show_view_names: false
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: none
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    defaults_version: 1
    series_types: {}
    show_null_points: true
    interpolation: linear
    listen: {}
    row: 51
    col: 12
    width: 12
    height: 3
  - title: Customer Behavior by Acquisition Source
    name: Customer Behavior by Acquisition Source
    model: omni_channel
    explore: omni_channel_events
    type: looker_column
    fields: [delivery_only, in_store_only, in_store_and_online, pickup_only, omni_channel_events.traffic_source]
    sorts: [delivery_only desc]
    limit: 500
    column_limit: 50
    dynamic_fields: [{measure: delivery_only, based_on: c360.customer_count, type: count_distinct,
        label: Delivery Only, value_format: !!null '', value_format_name: !!null '',
        _kind_hint: measure, _type_hint: number, filter_expression: "${c360.online_transaction_count}\
          \ > 0 AND ${c360.instore_transaction_count} = 0 AND ${c360.curbside_transaction_count}\
          \ = 0"}, {measure: in_store_only, based_on: c360.customer_count, type: count_distinct,
        label: In Store Only, value_format: !!null '', value_format_name: !!null '',
        _kind_hint: measure, _type_hint: number, filter_expression: "${c360.curbside_transaction_count}\
          \ = 0 AND ${c360.instore_transaction_count} > 0 AND ${c360.online_transaction_count}\
          \ = 0"}, {measure: in_store_and_online, based_on: c360.customer_count, type: count_distinct,
        label: In Store and Online, value_format: !!null '', value_format_name: !!null '',
        _kind_hint: measure, _type_hint: number, filter_expression: "${c360.instore_transaction_count}\
          \ > 0 AND ${c360.online_transaction_count} > 0"}, {measure: pickup_only,
        based_on: c360.customer_count, type: count_distinct, label: Pickup Only, value_format: !!null '',
        value_format_name: !!null '', _kind_hint: measure, _type_hint: number, filter_expression: "${c360.online_transaction_count}\
          \ >0 AND ${c360.curbside_transaction_count} >0 AND ${c360.instore_transaction_count}\
          \ =0"}]
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: normal
    limit_displayed_rows: false
    legend_position: center
    point_style: none
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    font_size: '12'
    series_types: {}
    defaults_version: 1
    show_null_points: true
    interpolation: linear
    listen: {}
    row: 35
    col: 0
    width: 12
    height: 8
  - title: Sales YoY
    name: Sales YoY
    model: omni_channel
    explore: omni_channel_transactions
    type: looker_line
    fields: [omni_channel_transactions__transaction_details.total_sales, omni_channel_transactions.transaction_month_name,
      omni_channel_transactions.transaction_year]
    pivots: [omni_channel_transactions.transaction_year]
    fill_fields: [omni_channel_transactions.transaction_month_name, omni_channel_transactions.transaction_year]
    sorts: [omni_channel_transactions.transaction_year 0, omni_channel_transactions.transaction_month_name]
    limit: 500
    column_limit: 50
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: false
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: circle
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    show_null_points: false
    interpolation: monotone
    y_axes: [{label: '', orientation: left, series: [{axisId: Assisted Checkout -
              omni_channel_transactions.transaction_count, id: Assisted Checkout -
              omni_channel_transactions.transaction_count, name: Assisted Checkout},
          {axisId: Delivery - omni_channel_transactions.transaction_count, id: Delivery
              - omni_channel_transactions.transaction_count, name: Delivery}, {axisId: In-store
              Pickup - omni_channel_transactions.transaction_count, id: In-store Pickup
              - omni_channel_transactions.transaction_count, name: In-store Pickup},
          {axisId: Self Checkout - omni_channel_transactions.transaction_count, id: Self
              Checkout - omni_channel_transactions.transaction_count, name: Self Checkout}],
        showLabels: false, showValues: true, unpinAxis: false, tickDensity: default,
        tickDensityCustom: 5, type: linear}]
    series_types: {}
    show_totals_labels: true
    show_silhouette: false
    totals_color: "#808080"
    defaults_version: 1
    listen: {}
    row: 5
    col: 12
    width: 12
    height: 9
  - title: New Customers
    name: New Customers
    model: omni_channel
    explore: omni_channel_transactions
    type: single_value
    fields: [c360.customer_count]
    filters:
      c360.first_purchase_date: 90 days
    limit: 500
    column_limit: 50
    dynamic_fields: [{table_calculation: goal, label: Goal, expression: '1000', value_format: !!null '',
        value_format_name: decimal_0, _kind_hint: dimension, _type_hint: number}]
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: true
    comparison_type: progress_percentage
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    defaults_version: 1
    listen: {}
    row: 2
    col: 12
    width: 6
    height: 3
  - title: Transactions
    name: Transactions
    model: omni_channel
    explore: omni_channel_transactions
    type: single_value
    fields: [omni_channel_transactions.transaction_count, omni_channel_transactions.reporting_period]
    filters:
      omni_channel_transactions.transaction_date: 2 years
    sorts: [omni_channel_transactions.transaction_count desc]
    limit: 500
    column_limit: 50
    dynamic_fields: [{table_calculation: from_last_year, label: from last year, expression: "${omni_channel_transactions.transaction_count}/offset(${omni_channel_transactions.transaction_count},1)\
          \ - 1", value_format: !!null '', value_format_name: percent_1, _kind_hint: measure,
        _type_hint: number}]
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: true
    comparison_type: change
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    defaults_version: 1
    hidden_fields: [omni_channel_transactions.reporting_period]
    listen: {}
    row: 2
    col: 18
    width: 6
    height: 3
  - title: Sales by Channel
    name: Sales by Channel
    model: omni_channel
    explore: omni_channel_transactions
    type: looker_pie
    fields: [c360.customer_type, omni_channel_transactions__transaction_details.total_sales]
    fill_fields: [c360.customer_type]
    limit: 500
    column_limit: 50
    row_total: right
    value_labels: legend
    label_type: labPer
    inner_radius: 45
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: false
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: normal
    limit_displayed_rows: false
    legend_position: center
    point_style: circle
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    show_null_points: false
    interpolation: monotone
    show_totals_labels: true
    show_silhouette: false
    totals_color: "#808080"
    y_axes: [{label: '', orientation: left, series: [{axisId: Assisted Checkout -
              omni_channel_transactions.transaction_count, id: Assisted Checkout -
              omni_channel_transactions.transaction_count, name: Assisted Checkout},
          {axisId: Delivery - omni_channel_transactions.transaction_count, id: Delivery
              - omni_channel_transactions.transaction_count, name: Delivery}, {axisId: In-store
              Pickup - omni_channel_transactions.transaction_count, id: In-store Pickup
              - omni_channel_transactions.transaction_count, name: In-store Pickup},
          {axisId: Self Checkout - omni_channel_transactions.transaction_count, id: Self
              Checkout - omni_channel_transactions.transaction_count, name: Self Checkout}],
        showLabels: false, showValues: true, unpinAxis: false, tickDensity: default,
        tickDensityCustom: 5, type: linear}]
    series_types: {}
    defaults_version: 1
    listen: {}
    row: 16
    col: 0
    width: 8
    height: 9
  - title: Profitability and CLV by Channel
    name: Profitability and CLV by Channel
    model: omni_channel
    explore: omni_channel_transactions
    type: looker_column
    fields: [c360.customer_type, c360.customer_count, omni_channel_transactions__transaction_details.profit_margin,
      retail_clv_predict.average_clv]
    fill_fields: [c360.customer_type]
    sorts: [c360.customer_count desc]
    limit: 500
    column_limit: 50
    row_total: right
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: false
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: circle
    show_value_labels: true
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    ordering: none
    show_null_labels: false
    show_totals_labels: true
    show_silhouette: false
    totals_color: "#808080"
    y_axes: [{label: '', orientation: left, series: [{axisId: retail_clv_predict.average_clv, id: retail_clv_predict.average_clv,
            name: Average Clv}], showLabels: false, showValues: false, unpinAxis: false,
        tickDensity: default, tickDensityCustom: 5, type: linear}, {label: '', orientation: left,
        series: [{axisId: c360.customer_count, id: c360.customer_count, name: Customer
              Count}], showLabels: false, showValues: false, unpinAxis: false, tickDensity: default,
        type: linear}, {label: !!null '', orientation: right, series: [{axisId: omni_channel_transactions__transaction_details.profit_margin,
            id: omni_channel_transactions__transaction_details.profit_margin, name: Profit
              Margin}], showLabels: false, showValues: false, unpinAxis: false, tickDensity: default,
        tickDensityCustom: 5, type: linear}]
    series_types: {}
    show_null_points: false
    interpolation: monotone
    value_labels: legend
    label_type: labPer
    inner_radius: 45
    defaults_version: 1
    listen: {}
    row: 16
    col: 8
    width: 8
    height: 9
  - title: In Store Customers
    name: In Store Customers
    model: omni_channel
    explore: omni_channel_transactions
    type: single_value
    fields: [c360.customer_count]
    filters:
      c360.customer_type: Instore Only
    limit: 500
    column_limit: 50
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    defaults_version: 1
    listen: {}
    row: 2
    col: 0
    width: 4
    height: 3
  - title: Online Customers
    name: Online Customers
    model: omni_channel
    explore: omni_channel_transactions
    type: single_value
    fields: [c360.customer_count]
    filters:
      c360.customer_type: Online Only
    limit: 500
    column_limit: 50
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    defaults_version: 1
    listen: {}
    row: 2
    col: 4
    width: 4
    height: 3
  - title: LTV by Channel
    name: LTV by Channel
    model: omni_channel
    explore: omni_channel_transactions
    type: looker_line
    fields: [c360.months_since_first_purchase, c360.customer_count, omni_channel_transactions__transaction_details.total_sales,
      c360.customer_type]
    pivots: [c360.customer_type]
    fill_fields: [c360.customer_type]
    filters:
      c360.months_since_first_purchase: ">0"
    sorts: [c360.customer_type 0, c360.months_since_first_purchase]
    limit: 500
    dynamic_fields: [{table_calculation: average_per_customer_sales, label: Average
          Per Customer Sales, expression: 'running_total(${omni_channel_transactions__transaction_details.total_sales}/index(${c360.customer_count},1))',
        value_format: !!null '', value_format_name: usd, _kind_hint: measure, _type_hint: number}]
    query_timezone: America/Los_Angeles
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: none
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    show_null_points: true
    interpolation: linear
    y_axes: [{label: Average Lifetime Sales, orientation: left, series: [{axisId: average_per_customer_sales,
            id: Online Only - 0 - average_per_customer_sales, name: Online Only},
          {axisId: average_per_customer_sales, id: Instore Only - 1 - average_per_customer_sales,
            name: Instore Only}, {axisId: average_per_customer_sales, id: Both Online
              and Instore - 2 - average_per_customer_sales, name: Both Online and
              Instore}], showLabels: true, showValues: false, unpinAxis: false, tickDensity: default,
        tickDensityCustom: 5, type: linear}]
    series_types: {}
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    defaults_version: 1
    hidden_fields: [c360.customer_count, omni_channel_transactions__transaction_details.total_sales]
    listen: {}
    row: 16
    col: 16
    width: 8
    height: 9
  - title: LTV by Acquisition Source
    name: LTV by Acquisition Source
    model: omni_channel
    explore: omni_channel_transactions
    type: looker_line
    fields: [c360.months_since_first_purchase, c360.customer_count, omni_channel_transactions__transaction_details.total_sales,
      c360.acquisition_source]
    pivots: [c360.acquisition_source]
    filters:
      c360.months_since_first_purchase: ">0"
      c360.acquisition_source: "-EMPTY"
    sorts: [c360.months_since_first_purchase, c360.acquisition_source]
    limit: 500
    dynamic_fields: [{table_calculation: average_per_customer_sales, label: Average
          Per Customer Sales, expression: 'running_total(${omni_channel_transactions__transaction_details.total_sales}/index(${c360.customer_count},1))',
        value_format: !!null '', value_format_name: usd, _kind_hint: measure, _type_hint: number}]
    query_timezone: America/Los_Angeles
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: none
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    show_null_points: true
    interpolation: linear
    series_types: {}
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    defaults_version: 1
    hidden_fields: [c360.customer_count, omni_channel_transactions__transaction_details.total_sales]
    listen: {}
    row: 27
    col: 12
    width: 12
    height: 8
  - title: Acquisition Source
    name: Acquisition Source
    model: omni_channel
    explore: omni_channel_transactions
    type: looker_donut_multiples
    fields: [c360.acquisition_source, c360.customer_count, c360.customer_type]
    pivots: [c360.acquisition_source]
    fill_fields: [c360.customer_type]
    sorts: [c360.customer_count desc 0, c360.customer_type, c360.acquisition_source]
    limit: 500
    column_limit: 50
    show_value_labels: false
    font_size: 12
    value_labels: legend
    label_type: labPer
    inner_radius: 45
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: none
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    defaults_version: 1
    series_types: {}
    row: 27
    col: 0
    width: 12
    height: 8
  - title: Website Activity by Traffic Source
    name: Website Activity by Traffic Source
    model: omni_channel
    explore: omni_channel_transactions
    type: looker_column
    fields: [c360.acquisition_source, session_count, cart_adds, purchases]
    filters:
      c360.acquisition_source: "-Unknown"
    sorts: [session_count desc]
    limit: 500
    column_limit: 50
    dynamic_fields: [{measure: purchases, based_on: c360.purchases, type: sum, label: Purchases,
        expression: !!null '', value_format: !!null '', value_format_name: !!null '',
        _kind_hint: measure, _type_hint: number}, {measure: cart_adds, based_on: c360.cart_adds,
        type: sum, label: Cart Adds, expression: !!null '', value_format: !!null '',
        value_format_name: !!null '', _kind_hint: measure, _type_hint: number}, {
        measure: session_count, based_on: c360.session_count, type: sum, label: Session
          Count, expression: !!null '', value_format: !!null '', value_format_name: !!null '',
        _kind_hint: measure, _type_hint: number}, {table_calculation: conversion_rate,
        label: Conversion Rate, expression: "${purchases} / ${session_count}", value_format: !!null '',
        value_format_name: percent_1, _kind_hint: measure, _type_hint: number}]
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: none
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    y_axes: [{label: '', orientation: left, series: [{axisId: session_count, id: session_count,
            name: Session Count}, {axisId: cart_adds, id: cart_adds, name: Cart Adds},
          {axisId: purchases, id: purchases, name: Purchases}], showLabels: true,
        showValues: true, unpinAxis: false, tickDensity: default, tickDensityCustom: 5,
        type: linear}, {label: !!null '', orientation: right, series: [{axisId: conversion_rate,
            id: conversion_rate, name: Conversion Rate}], showLabels: true, showValues: true,
        unpinAxis: true, tickDensity: default, tickDensityCustom: 5, type: linear}]
    font_size: '12'
    series_types:
      conversion_rate: line
    value_labels: legend
    label_type: labPer
    inner_radius: 45
    defaults_version: 1
    listen: {}
    row: 35
    col: 12
    width: 12
    height: 8
