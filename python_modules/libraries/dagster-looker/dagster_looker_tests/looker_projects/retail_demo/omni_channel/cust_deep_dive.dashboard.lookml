- dashboard: customer_deep_dive
  title: Customer Deep Dive
  layout: newspaper
  preferred_viewer: dashboards
  elements:
  - title: Customer Location
    name: Customer Location
    model: omni_channel
    explore: omni_channel_transactions
    type: looker_geo_coordinates
    fields: [customers.location, c360.customer_count]
    sorts: [customers.location]
    limit: 500
    column_limit: 50
    map: usa
    map_projection: ''
    show_view_names: false
    point_radius: 10
    map_plot_mode: points
    heatmap_gridlines: false
    heatmap_gridlines_empty: false
    heatmap_opacity: 0.5
    show_region_field: true
    draw_map_labels_above_data: true
    map_tile_provider: light
    map_position: fit_data
    map_scale_indicator: 'off'
    map_pannable: true
    map_zoomable: true
    map_marker_type: icon
    map_marker_icon_name: default
    map_marker_radius_mode: fixed
    map_marker_units: pixels
    map_marker_proportional_scale_type: linear
    map_marker_color_mode: fixed
    show_legend: true
    quantize_map_value_colors: false
    reverse_map_value_colors: false
    map_zoom: 8
    map_marker_radius_fixed: 10
    defaults_version: 1
    series_types: {}
    listen:
      ID: c360.customer_id
    row: 0
    col: 12
    width: 12
    height: 8
  - title: Customer Info
    name: Customer Info
    model: omni_channel
    explore: omni_channel_transactions
    type: looker_single_record
    fields: [customers.id, customers.name, customers.registered_date, customers.email,
      customers.age, customers.gender, customers.city, customers.state, customers.postcode]
    sorts: [customers.registered_date desc]
    limit: 500
    column_limit: 50
    show_view_names: false
    show_sql_query_menu_options: false
    show_totals: false
    show_row_totals: false
    show_row_numbers: false
    transpose: false
    truncate_text: true
    size_to_fit: true
    table_theme: white
    limit_displayed_rows: false
    enable_conditional_formatting: false
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    series_types: {}
    hide_totals: false
    hide_row_totals: false
    defaults_version: 1
    listen:
      ID: c360.customer_id
    row: 0
    col: 0
    width: 6
    height: 6
  - title: Lifetime Purchases
    name: Lifetime Purchases
    model: omni_channel
    explore: omni_channel_transactions
    type: single_value
    fields: [c360.transaction_count]
    limit: 500
    column_limit: 50
    dynamic_fields: [{table_calculation: calculation_1, label: Calculation 1, expression: "${c360.purchases}\
          \ / ${c360.cart_adds}", value_format: !!null '', value_format_name: percent_1,
        _kind_hint: dimension, _type_hint: number, is_disabled: true}]
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    comparison_label: Conversion Rate
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
    defaults_version: 1
    series_types: {}
    hidden_fields: []
    listen:
      ID: c360.customer_id
    row: 0
    col: 6
    width: 6
    height: 2
  - title: Lifetime Returns
    name: Lifetime Returns
    model: omni_channel
    explore: omni_channel_transactions
    type: single_value
    fields: [c360.return_count]
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
    defaults_version: 1
    series_types: {}
    listen:
      ID: c360.customer_id
    row: 6
    col: 6
    width: 6
    height: 2
  - title: Total Sales
    name: Total Sales
    model: omni_channel
    explore: omni_channel_transactions
    type: single_value
    fields: [c360.total_sales]
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
    defaults_version: 1
    series_types: {}
    listen:
      ID: c360.customer_id
    row: 2
    col: 6
    width: 6
    height: 2
  - title: Predicted CLV
    name: Predicted CLV
    model: omni_channel
    explore: omni_channel_transactions
    type: single_value
    fields: [c360.predicted_clv]
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
    defaults_version: 1
    series_types: {}
    listen:
      ID: c360.customer_id
    row: 4
    col: 6
    width: 6
    height: 2
  - title: Churn Risk
    name: Churn Risk
    model: omni_channel
    explore: omni_channel_transactions
    type: single_value
    fields: [c360.risk_of_churn]
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
    defaults_version: 1
    series_types: {}
    listen:
      ID: c360.customer_id
    row: 6
    col: 0
    width: 6
    height: 2
  - title: Order History
    name: Order History
    model: omni_channel
    explore: omni_channel_transactions
    type: looker_grid
    fields: [omni_channel_transactions.transaction_date, omni_channel_transactions.transaction_id,
      omni_channel_transactions.purchase_channel, omni_channel_transactions.fulfillment_channel,
      omni_channel_transactions.offer_type, omni_channel_transactions.store_name,
      omni_channel_transactions__transaction_details.product_name, omni_channel_transactions__transaction_details.product_sku,
      omni_channel_transactions__transaction_details.sale_price]
    sorts: [omni_channel_transactions.transaction_date desc]
    limit: 500
    column_limit: 50
    show_view_names: false
    show_row_numbers: false
    transpose: false
    truncate_text: false
    hide_totals: false
    hide_row_totals: false
    size_to_fit: true
    table_theme: white
    limit_displayed_rows: false
    enable_conditional_formatting: false
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    show_sql_query_menu_options: false
    show_totals: false
    show_row_totals: false
    series_labels:
      omni_channel_transactions.transaction_date: Date
      omni_channel_transactions.transaction_id: ID
    series_types: {}
    defaults_version: 1
    listen:
      ID: omni_channel_transactions.customer_id
    row: 8
    col: 0
    width: 12
    height: 14
  - name: Customer Timeline
    title: Customer Timeline
    merged_queries:
    - model: omni_channel
      explore: omni_channel_transactions
      type: table
      fields: [omni_channel_transactions.transaction_date, omni_channel_transactions.transaction_count]
      fill_fields: [omni_channel_transactions.transaction_date]
      limit: 500
      query_timezone: America/Los_Angeles
      join_fields: []
    - model: omni_channel
      explore: omni_channel_events
      type: table
      fields: [omni_channel_events.session_count, omni_channel_events.created_date]
      fill_fields: [omni_channel_events.created_date]
      limit: 500
      query_timezone: America/Los_Angeles
      join_fields:
      - field_name: omni_channel_events.created_date
        source_field_name: omni_channel_transactions.transaction_date
    - model: omni_channel
      explore: omni_channel_support_calls
      type: table
      fields: [omni_channel_support_calls.conversation_start_date, omni_channel_support_calls.count]
      fill_fields: [omni_channel_support_calls.conversation_start_date]
      sorts: [omni_channel_support_calls.conversation_start_date desc]
      limit: 500
      query_timezone: America/Los_Angeles
      join_fields:
      - field_name: omni_channel_support_calls.conversation_start_date
        source_field_name: omni_channel_transactions.transaction_date
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    y_axes: [{label: '', orientation: left, series: [{axisId: omni_channel_transactions.transaction_count,
            id: omni_channel_transactions.transaction_count, name: Purchases}, {axisId: omni_channel_events.session_count,
            id: omni_channel_events.session_count, name: Web Visits}, {axisId: omni_channel_support_calls.count,
            id: omni_channel_support_calls.count, name: Support Calls}], showLabels: false,
        showValues: false, maxValue: 1, minValue: 1, unpinAxis: true, tickDensity: default,
        tickDensityCustom: 5, type: linear}]
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
    series_types: {}
    point_style: circle
    series_labels:
      omni_channel_transactions.transaction_count: Purchases
      omni_channel_events.session_count: Web Visits
      omni_channel_support_calls.count: Support Calls
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    x_axis_datetime_label: "%b-%y"
    y_axis_combined: true
    show_null_points: false
    type: looker_scatter
    listen:
    - ID: c360.customer_id
    - ID: c360.customer_id
    - ID: omni_channel_support_calls.client_id
    row: 8
    col: 12
    width: 12
    height: 7
  filters:
  - name: ID
    title: ID
    type: field_filter
    default_value: '81359'
    allow_multiple_values: true
    required: false
    model: omni_channel
    explore: customer_transaction_fact
    listens_to_filters: []
    field: customer_event_fact.customer_id
