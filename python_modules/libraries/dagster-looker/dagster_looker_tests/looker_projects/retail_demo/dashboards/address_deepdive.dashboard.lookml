- dashboard: address_deepdive
  title: Address Deep-dive
  layout: newspaper
  elements:
  - title: Location
    name: Location
    model: retail_block_model
    explore: transactions
    type: looker_map
    fields: [customers.location]
    filters:
      transactions.transaction_date: 720 days
    sorts: [customers.location]
    limit: 500
    column_limit: 50
    map_plot_mode: points
    heatmap_gridlines: false
    heatmap_gridlines_empty: false
    heatmap_opacity: 0.5
    show_region_field: true
    draw_map_labels_above_data: true
    map_tile_provider: traffic_day
    map_position: fit_data
    map_zoom: 20
    map_scale_indicator: metric_imperial
    map_pannable: true
    map_zoomable: true
    map_marker_type: icon
    map_marker_icon_name: default
    map_marker_radius_mode: proportional_value
    map_marker_units: meters
    map_marker_proportional_scale_type: linear
    map_marker_color_mode: fixed
    show_view_names: false
    show_legend: true
    quantize_map_value_colors: false
    reverse_map_value_colors: false
    series_types: {}
    listen:
      Address: customers.address
    row: 4
    col: 0
    width: 8
    height: 6
  - title: Address Street View
    name: Address Street View
    model: retail_block_model
    explore: transactions
    type: single_value
    fields: [customers.address_street_view]
    filters:
      transactions.transaction_date: 720 days
    sorts: [customers.address_street_view]
    limit: 500
    column_limit: 50
    series_types: {}
    listen:
      Address: customers.address
    row: 4
    col: 8
    width: 16
    height: 10
  - title: Registered customers at this address
    name: Registered customers at this address
    model: retail_block_model
    explore: transactions
    type: single_value
    fields: [customers.address_comparison, transactions__line_items.number_of_customers_per_address]
    filters:
      transactions.transaction_date: 720 days
    sorts: [customers.address_comparison]
    limit: 500
    dynamic_fields: [{table_calculation: vs_average, label: vs Average, expression: "${transactions__line_items.number_of_customers_per_address}-if(is_null(offset(${transactions__line_items.number_of_customers_per_address},1)),0,offset(${transactions__line_items.number_of_customers_per_address},1))",
        value_format: !!null '', value_format_name: decimal_0, _kind_hint: measure,
        _type_hint: number}]
    query_timezone: America/Los_Angeles
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: true
    comparison_type: change
    comparison_reverse_colors: true
    show_comparison_label: true
    comparison_label: vs Average
    enable_conditional_formatting: false
    conditional_formatting: [{type: equal to, value: !!null '', background_color: "#5A30C2",
        font_color: !!null '', color_application: {collection_id: retailer-scheme,
          palette_id: retailer-scheme-sequential-0}, bold: false, italic: false, strikethrough: false,
        fields: !!null ''}]
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    series_types: {}
    hidden_fields: [customers.address_comparison]
    listen:
      Address: customers.address_comparison_filter
    row: 10
    col: 0
    width: 8
    height: 4
  - title: Order Pattern
    name: Order Pattern
    model: retail_block_model
    explore: transactions
    type: looker_line
    fields: [transactions.transaction_date, transactions__line_items.total_quantity,
      transactions__line_items.total_sales]
    fill_fields: [transactions.transaction_date]
    filters: {}
    sorts: [transactions.transaction_date desc]
    limit: 500
    query_timezone: America/Los_Angeles
    color_application:
      collection_id: f14810d2-98d7-42df-82d0-bc185a074e42
      custom:
        id: fb62237b-4172-a396-b394-be13521b401d
        label: Custom
        type: discrete
        colors:
        - "#5A30C2"
        - "#9d81e6"
      options:
        steps: 5
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    y_axes: [{label: '', orientation: left, series: [{axisId: transactions__line_items.total_quantity,
            id: transactions__line_items.total_quantity, name: Total Quantity}], showLabels: true,
        showValues: true, unpinAxis: false, tickDensity: default, type: linear}, {
        label: !!null '', orientation: right, series: [{axisId: transactions__line_items.total_sales,
            id: transactions__line_items.total_sales, name: Total Sales}], showLabels: true,
        showValues: true, unpinAxis: false, tickDensity: default, type: linear}]
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
    series_types:
      transactions__line_items.total_quantity: scatter
      transactions__line_items.total_sales: column
    point_style: circle_outline
    series_colors: {}
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    show_null_points: false
    interpolation: linear
    listen:
      Address: customers.address
      Date Range: transactions.transaction_date
    row: 14
    col: 0
    width: 12
    height: 8
  - title: Most Ordered Items
    name: Most Ordered Items
    model: retail_block_model
    explore: transactions
    type: looker_grid
    fields: [transactions__line_items.total_quantity, transactions__line_items.average_item_price,
      products.name, products.product_image, products.category]
    filters: {}
    sorts: [transactions__line_items.total_quantity desc]
    limit: 500
    query_timezone: America/Los_Angeles
    show_totals: true
    show_row_totals: true
    show_view_names: false
    show_row_numbers: true
    transpose: false
    truncate_text: false
    size_to_fit: true
    series_cell_visualizations:
      transactions__line_items.total_quantity:
        is_active: true
        palette:
          palette_id: b8916b58-92d8-1cc3-f7a2-03bbcbc3635d
          collection_id: f14810d2-98d7-42df-82d0-bc185a074e42
          custom_colors:
          - "#ffffff"
          - "#9d81e6"
          - "#5A30C2"
    table_theme: white
    limit_displayed_rows: false
    enable_conditional_formatting: false
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    truncate_column_names: false
    hide_totals: false
    hide_row_totals: false
    x_axis_gridlines: false
    y_axis_gridlines: true
    y_axes: [{label: '', orientation: left, series: [{axisId: transactions__line_items.total_quantity,
            id: transactions__line_items.total_quantity, name: Total Quantity}], showLabels: true,
        showValues: true, unpinAxis: false, tickDensity: default, type: linear}, {
        label: !!null '', orientation: right, series: [{axisId: transactions__line_items.total_sales,
            id: transactions__line_items.total_sales, name: Total Sales}], showLabels: true,
        showValues: true, unpinAxis: false, tickDensity: default, type: linear}]
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
    legend_position: center
    series_types: {}
    point_style: circle_outline
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    show_null_points: false
    interpolation: linear
    listen:
      Address: customers.address
      Date Range: transactions.transaction_date
    row: 14
    col: 12
    width: 12
    height: 8
  - name: "<span class='fa fa-map-pin'> Address Overview</span>"
    type: text
    title_text: "<span class='fa fa-map-pin'> Address Overview</span>"
    subtitle_text: <font color="#5b30c2">Are there any strange patterns happening
      at this address?</font>
    body_text: |-
      <center><strong>Recommended Action ?</strong>
      Check if the address does not look residential, or has an abnormally high number of registered customers or volume. If so, set up a regular alert to monitor it, and alert the fraud team if the pattern continues ?.</center>
    row: 0
    col: 0
    width: 24
    height: 4
  filters:
  - name: Address
    title: Address
    type: field_filter
    default_value: '"1909 W 95th St, Chicago, IL 60643, United States"'
    allow_multiple_values: true
    required: false
    model: retail_block_model
    explore: transactions
    listens_to_filters: []
    field: customers.address
  - name: Date Range
    title: Date Range
    type: date_filter
    default_value: 90 days
    allow_multiple_values: true
    required: false
