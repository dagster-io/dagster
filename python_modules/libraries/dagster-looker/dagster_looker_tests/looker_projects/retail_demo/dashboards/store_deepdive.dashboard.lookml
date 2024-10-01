- dashboard: store_deepdive
  title: Store Deep-dive
  layout: newspaper
  elements:
  - title: Sales
    name: Sales
    model: retail_block_model
    explore: transactions
    type: single_value
    fields: [transactions.selected_comparison, transactions__line_items.total_sales,
      transactions.number_of_transactions, transactions__line_items.average_basket_size,
      transactions.percent_customer_transactions]
    filters:
      transactions.transaction_date: 2 years
      transactions.comparison_type: year
      transactions.selected_comparison: "-NULL"
    sorts: [transactions.selected_comparison desc]
    limit: 500
    column_limit: 50
    dynamic_fields: [{table_calculation: vs_ly, label: vs LY, expression: "${transactions__line_items.total_sales}/offset(${transactions__line_items.total_sales},1)-1",
        value_format: !!null '', value_format_name: percent_1, _kind_hint: measure,
        _type_hint: number}, {table_calculation: target, label: Target, expression: 'round(${transactions__line_items.total_sales}*1.1/10000,0)*10000',
        value_format: !!null '', value_format_name: usd_0, _kind_hint: measure, _type_hint: number}]
    custom_color_enabled: true
    custom_color: "#5A30C2"
    show_single_value_title: true
    show_comparison: true
    comparison_type: progress_percentage
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    series_types: {}
    hidden_fields: [transactions.number_of_transactions, transactions__line_items.average_basket_size,
      transactions.percent_customer_transactions, vs_ly]
    listen:
      Date: transactions.date_comparison_filter
      Store: stores.name
    row: 0
    col: 0
    width: 6
    height: 4
  - title: Transactions
    name: Transactions
    model: retail_block_model
    explore: transactions
    type: single_value
    fields: [transactions.selected_comparison, transactions__line_items.total_sales,
      transactions.number_of_transactions, transactions__line_items.average_basket_size,
      transactions.percent_customer_transactions]
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
    hidden_fields: [transactions__line_items.average_basket_size, transactions.percent_customer_transactions,
      transactions__line_items.total_sales]
    listen:
      Date: transactions.date_comparison_filter
      Store: stores.name
    row: 0
    col: 6
    width: 6
    height: 4
  - title: Basket Size
    name: Basket Size
    model: retail_block_model
    explore: transactions
    type: single_value
    fields: [transactions.selected_comparison, transactions__line_items.total_sales,
      transactions.number_of_transactions, transactions__line_items.average_basket_size,
      transactions.percent_customer_transactions]
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
    hidden_fields: [transactions.percent_customer_transactions, transactions__line_items.total_sales,
      transactions.number_of_transactions]
    listen:
      Date: transactions.date_comparison_filter
      Store: stores.name
    row: 0
    col: 12
    width: 6
    height: 4
  - title: "% Trx from Loyalty"
    name: "% Trx from Loyalty"
    model: retail_block_model
    explore: transactions
    type: single_value
    fields: [transactions.selected_comparison, transactions__line_items.total_sales,
      transactions.number_of_transactions, transactions__line_items.average_basket_size,
      transactions.percent_customer_transactions]
    filters:
      transactions.transaction_date: 2 years
      transactions.comparison_type: year
      transactions.selected_comparison: "-NULL"
    sorts: [transactions.selected_comparison desc]
    limit: 500
    column_limit: 50
    dynamic_fields: [{table_calculation: vs_ly, label: vs LY, expression: "${transactions.percent_customer_transactions}-offset(${transactions.percent_customer_transactions},1)",
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
      Date: transactions.date_comparison_filter
      Store: stores.name
    row: 0
    col: 18
    width: 6
    height: 4
  - name: "<span class='fa fa-flag-checkered'> Peer Store Comparison</span>"
    type: text
    title_text: "<span class='fa fa-flag-checkered'> Peer Store Comparison</span>"
    subtitle_text: <font color="#5b30c2">How well am I doing vs my peer stores?</font>
    body_text: |-
      <center><strong>Recommended Action ?</strong>
      Text/call high-performing store managers to see if they have any advice. Check if different weather trends are affecting your performance as much as in your peer stores.</center>
    row: 4
    col: 0
    width: 24
    height: 4
  - name: "<span class='fa fa-users'> Customer Behaviour</span>"
    type: text
    title_text: "<span class='fa fa-users'> Customer Behaviour</span>"
    subtitle_text: <font color="#5b30c2">How am I performing with my target customer
      segments?</font>
    body_text: |-
      <center><strong>Recommended Action ?</strong>
      Look for segments with low performance (YoY or vs peer stores), and drill into them to see possible actions to drive them back to our store.</center>
    row: 45
    col: 0
    width: 24
    height: 4
  - title: Emerging Millennials ?
    name: Emerging Millennials ?
    model: retail_block_model
    explore: transactions
    type: single_value
    fields: [transactions.selected_comparison, transactions__line_items.total_sales,
      transactions.number_of_transactions, transactions__line_items.average_basket_size]
    filters:
      transactions.transaction_date: 2 years
      transactions.comparison_type: year
      transactions.selected_comparison: "-NULL"
      customer_clustering_prediction.customer_segment: Emerging Millennials ?
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
    hidden_fields: [transactions.number_of_transactions, transactions__line_items.average_basket_size]
    listen:
      Date: transactions.date_comparison_filter
      Store: stores.name
    row: 49
    col: 0
    width: 6
    height: 4
  - title: Regular Gen Xers ?
    name: Regular Gen Xers ?
    model: retail_block_model
    explore: transactions
    type: single_value
    fields: [transactions.selected_comparison, transactions__line_items.total_sales,
      transactions.number_of_transactions, transactions__line_items.average_basket_size]
    filters:
      transactions.transaction_date: 2 years
      transactions.comparison_type: year
      transactions.selected_comparison: "-NULL"
      customer_clustering_prediction.customer_segment: Regular Gen Xers ?
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
    hidden_fields: [transactions.number_of_transactions, transactions__line_items.average_basket_size]
    listen:
      Date: transactions.date_comparison_filter
      Store: stores.name
    row: 49
    col: 6
    width: 6
    height: 4
  - title: One-off locals ?
    name: One-off locals ?
    model: retail_block_model
    explore: transactions
    type: single_value
    fields: [transactions.selected_comparison, transactions__line_items.total_sales,
      transactions.number_of_transactions, transactions__line_items.average_basket_size]
    filters:
      transactions.transaction_date: 2 years
      transactions.comparison_type: year
      transactions.selected_comparison: "-NULL"
      customer_clustering_prediction.customer_segment: One-off locals ?
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
    hidden_fields: [transactions.number_of_transactions, transactions__line_items.average_basket_size]
    note_state: expanded
    note_display: below
    note_text: ''
    listen:
      Date: transactions.date_comparison_filter
      Store: stores.name
    row: 53
    col: 6
    width: 6
    height: 5
  - title: Affluent Retirees ?
    name: Affluent Retirees ?
    model: retail_block_model
    explore: transactions
    type: single_value
    fields: [transactions.selected_comparison, transactions__line_items.total_sales,
      transactions.number_of_transactions, transactions__line_items.average_basket_size]
    filters:
      transactions.transaction_date: 2 years
      transactions.comparison_type: year
      transactions.selected_comparison: "-NULL"
      customer_clustering_prediction.customer_segment: Affluent Retirees ?
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
    hidden_fields: [transactions.number_of_transactions, transactions__line_items.average_basket_size]
    listen:
      Date: transactions.date_comparison_filter
      Store: stores.name
    row: 53
    col: 0
    width: 6
    height: 5
  - title: YoY Sales
    name: YoY Sales
    model: retail_block_model
    explore: transactions
    type: looker_bar
    fields: [transactions__line_items.sales_change, transactions.number_of_transactions_change,
      stores.store_comparison_vs_stores_in_tier_with_weather]
    filters:
      transactions.transaction_date: 2 years
      transactions.comparison_type: year
    sorts: [transactions__line_items.sales_change desc]
    limit: 500
    column_limit: 50
    dynamic_fields: [{table_calculation: store, label: Store, expression: 'concat(${stores.store_comparison_vs_stores_in_tier},"
          ",${weather})', value_format: !!null '', value_format_name: !!null '', is_disabled: true,
        _kind_hint: dimension, _type_hint: string}, {table_calculation: focus_store_sales_change,
        label: Focus Store Sales Change (%), expression: 'if(contains(${stores.store_comparison_vs_stores_in_tier_with_weather},"1-
          "),${transactions__line_items.sales_change},null)', value_format: !!null '',
        value_format_name: percent_1, _kind_hint: measure, _type_hint: number}, {
        table_calculation: other_stores_sales_change, label: Other Stores Sales Change
          (%), expression: 'if(contains(${stores.store_comparison_vs_stores_in_tier_with_weather},"1-
          "),null,${transactions__line_items.sales_change})', value_format: !!null '',
        value_format_name: percent_1, _kind_hint: measure, _type_hint: number}, {
        table_calculation: weather, label: Weather, expression: 'if(${store_weather.average_daily_precipitation}<2.0,"☀️",if(${store_weather.average_daily_precipitation}<4.0,"☁️","?"))',
        value_format: !!null '', value_format_name: !!null '', is_disabled: true,
        _kind_hint: dimension, _type_hint: string}]
    color_application:
      collection_id: f14810d2-98d7-42df-82d0-bc185a074e42
      palette_id: 89f8fd99-5003-4efd-ae1a-ae0aa28825ca
      options:
        steps: 5
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
    series_types: {}
    point_style: circle
    series_colors:
      focus_store_sales_change: "#5A30C2"
      other_stores_sales_change: "#9d81e6"
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    show_row_numbers: true
    transpose: false
    truncate_text: true
    hide_totals: false
    hide_row_totals: false
    size_to_fit: true
    series_cell_visualizations:
      focus_store_sales_change:
        is_active: false
      other_stores_sales_change:
        is_active: true
    table_theme: white
    enable_conditional_formatting: false
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
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
    map_marker_type: circle
    map_marker_icon_name: default
    map_marker_radius_mode: proportional_value
    map_marker_units: pixels
    map_marker_radius_min: 3
    map_marker_radius_max: 20
    map_marker_proportional_scale_type: linear
    map_marker_color_mode: value
    show_legend: true
    map_value_colors: ["#aaa", "#5930c2"]
    quantize_map_value_colors: false
    reverse_map_value_colors: false
    color_range: ["#5A30C2", "#9d81e6", "#2D2442", "#42248F", "#1F1142"]
    color_by: root
    show_null_points: true
    hidden_fields: [transactions__line_items.sales_change, transactions.number_of_transactions_change]
    note_state: collapsed
    note_display: hover
    note_text: This shows your year over year sales
    listen:
      Date: transactions.date_comparison_filter
      Store: stores.store_for_comparison
    row: 8
    col: 0
    width: 12
    height: 8
  - title: YoY Transaction Count
    name: YoY Transaction Count
    model: retail_block_model
    explore: transactions
    type: looker_bar
    fields: [stores.store_comparison_vs_stores_in_tier_with_weather, transactions__line_items.sales_change,
      transactions.number_of_transactions_change]
    filters:
      transactions.transaction_date: 2 years
      transactions.comparison_type: year
    sorts: [transactions.number_of_transactions_change desc]
    limit: 500
    column_limit: 50
    dynamic_fields: [{table_calculation: focus_store_transaction_count_change, label: Focus
          Store Transaction Count Change (%), expression: 'if(contains(${stores.store_comparison_vs_stores_in_tier_with_weather},"1-
          "),${transactions.number_of_transactions_change},null)', value_format: !!null '',
        value_format_name: percent_1, _kind_hint: measure, _type_hint: number}, {
        table_calculation: other_stores_transaction_count_change, label: Other Stores
          Transaction Count Change (%), expression: 'if(contains(${stores.store_comparison_vs_stores_in_tier_with_weather},"1-
          "),null,${transactions.number_of_transactions_change})', value_format: !!null '',
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
    stacking: normal
    limit_displayed_rows: false
    legend_position: center
    series_types: {}
    point_style: circle
    series_colors:
      other_stores_transaction_count_change: "#9d81e6"
      focus_store_transaction_count_change: "#5A30C2"
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    show_row_numbers: true
    transpose: false
    truncate_text: true
    hide_totals: false
    hide_row_totals: false
    size_to_fit: true
    series_cell_visualizations:
      focus_store_sales_change:
        is_active: false
      other_stores_sales_change:
        is_active: true
    table_theme: white
    enable_conditional_formatting: false
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
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
    map_marker_type: circle
    map_marker_icon_name: default
    map_marker_radius_mode: proportional_value
    map_marker_units: pixels
    map_marker_radius_min: 3
    map_marker_radius_max: 20
    map_marker_proportional_scale_type: linear
    map_marker_color_mode: value
    show_legend: true
    map_value_colors: ["#aaa", "#5930c2"]
    quantize_map_value_colors: false
    reverse_map_value_colors: false
    color_range: ["#5A30C2", "#9d81e6", "#2D2442", "#42248F", "#1F1142"]
    color_by: root
    show_null_points: true
    hidden_fields: [transactions__line_items.sales_change, transactions.number_of_transactions_change]
    listen:
      Date: transactions.date_comparison_filter
      Store: stores.store_for_comparison
    row: 8
    col: 12
    width: 12
    height: 8
  - title: Weather Trend vs Sales Trend
    name: Weather Trend vs Sales Trend
    model: retail_block_model
    explore: transactions
    type: looker_line
    fields: [store_weather.average_max_temparature, transactions.transaction_date,
      transactions__line_items.total_sales_per_store]
    fill_fields: [transactions.transaction_date]
    filters:
      transactions.transaction_date: 14 days
      stores.store_comparison_vs_tier: 1-%
    sorts: [transactions.transaction_date desc]
    limit: 500
    column_limit: 1
    dynamic_fields: [{table_calculation: focus_store_transaction_count_change, label: Focus
          Store Transaction Count Change (%), expression: 'if(contains(${stores.store_comparison_vs_stores_in_tier_with_weather},"1-
          "),${transactions.number_of_transactions_change},null)', value_format: !!null '',
        value_format_name: percent_1, _kind_hint: measure, _type_hint: number, is_disabled: true},
      {table_calculation: other_stores_transaction_count_change, label: Other Stores
          Transaction Count Change (%), expression: 'if(contains(${stores.store_comparison_vs_stores_in_tier_with_weather},"1-
          "),null,${transactions.number_of_transactions_change})', value_format: !!null '',
        value_format_name: percent_1, _kind_hint: measure, _type_hint: number, is_disabled: true}]
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    y_axes: [{label: '', orientation: left, series: [{axisId: store_weather.average_max_temparature,
            id: store_weather.average_max_temparature, name: Average Max Temparature}],
        showLabels: true, showValues: true, unpinAxis: false, tickDensity: default,
        type: linear}, {label: '', orientation: right, series: [{axisId: transactions__line_items.total_sales_per_store,
            id: transactions__line_items.total_sales_per_store, name: Total Sales
              per Store}], showLabels: true, showValues: true, unpinAxis: false, tickDensity: default,
        type: linear}]
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
    hidden_series: []
    legend_position: center
    series_types: {}
    point_style: circle
    series_colors:
      1- Los Angeles - transactions__line_items.total_sales_per_store: "#1F1142"
      2- Rest of Stores in Tier - store_weather.average_max_temparature: "#5A30C2"
      2- Rest of Stores in Tier - transactions__line_items.total_sales_per_store: "#1F1142"
      transactions__line_items.total_sales_per_store: "#1F1142"
      store_weather.average_max_temparature: "#9d81e6"
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    reference_lines: [{reference_type: range, margin_top: deviation, margin_value: mean,
        margin_bottom: deviation, label_position: right, color: "#588eff", line_value: '10',
        range_start: "-10", range_end: '10', label: Cold}, {reference_type: range,
        line_value: mean, margin_top: deviation, margin_value: mean, margin_bottom: deviation,
        label_position: right, color: "#f0c157", range_start: '10', range_end: '20',
        label: Warm}, {reference_type: range, line_value: mean, margin_top: deviation,
        margin_value: mean, margin_bottom: deviation, label_position: right, color: "#ed5432",
        range_start: '20', range_end: '60', label: Hot}]
    show_null_points: false
    interpolation: linear
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    show_row_numbers: true
    transpose: false
    truncate_text: true
    hide_totals: false
    hide_row_totals: false
    size_to_fit: true
    series_cell_visualizations:
      focus_store_sales_change:
        is_active: false
      other_stores_sales_change:
        is_active: true
    table_theme: white
    enable_conditional_formatting: false
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
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
    map_marker_type: circle
    map_marker_icon_name: default
    map_marker_radius_mode: proportional_value
    map_marker_units: pixels
    map_marker_radius_min: 3
    map_marker_radius_max: 20
    map_marker_proportional_scale_type: linear
    map_marker_color_mode: value
    show_legend: true
    map_value_colors: ["#aaa", "#5930c2"]
    quantize_map_value_colors: false
    reverse_map_value_colors: false
    color_range: ["#5A30C2", "#9d81e6", "#2D2442", "#42248F", "#1F1142"]
    color_by: root
    hidden_fields: []
    listen:
      Store: stores.store_for_comparison
    row: 16
    col: 0
    width: 12
    height: 7
  - title: How well am I selling products that are doing well in my peer stores?
    name: How well am I selling products that are doing well in my peer stores?
    model: retail_block_model
    explore: transactions
    type: table
    fields: [stores.store_comparison_vs_tier, transactions__line_items.total_quantity_per_store,
      transactions.number_of_transactions_per_store, products.name]
    pivots: [stores.store_comparison_vs_tier]
    filters:
      transactions.transaction_date: 7 days
    sorts: [stores.store_comparison_vs_tier 0, transactions__line_items.total_quantity_per_store
        desc 1]
    limit: 500
    column_limit: 50
    dynamic_fields: [{table_calculation: focus_store_transaction_count_change, label: Focus
          Store Transaction Count Change (%), expression: 'if(contains(${stores.store_comparison_vs_stores_in_tier_with_weather},"1-
          "),${transactions.number_of_transactions_change},null)', value_format: !!null '',
        value_format_name: percent_1, _kind_hint: measure, _type_hint: number, is_disabled: true},
      {table_calculation: other_stores_transaction_count_change, label: Other Stores
          Transaction Count Change (%), expression: 'if(contains(${stores.store_comparison_vs_stores_in_tier_with_weather},"1-
          "),null,${transactions.number_of_transactions_change})', value_format: !!null '',
        value_format_name: percent_1, _kind_hint: measure, _type_hint: number, is_disabled: true}]
    show_view_names: false
    show_row_numbers: true
    truncate_column_names: false
    hide_totals: false
    hide_row_totals: false
    table_theme: white
    limit_displayed_rows: false
    enable_conditional_formatting: true
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    conditional_formatting: [{type: along a scale..., value: !!null '', background_color: "#5A30C2",
        font_color: !!null '', color_application: {collection_id: f14810d2-98d7-42df-82d0-bc185a074e42,
          custom: {id: c9dd1a4e-a553-d252-0a2b-98cd3e570d22, label: Custom, type: continuous,
            stops: [{color: "#fff", offset: 0}, {color: "#9d81e6", offset: 50}, {
                color: "#5930c2", offset: 100}]}, options: {steps: 5}}, bold: false,
        italic: false, strikethrough: false, fields: [transactions__line_items.total_quantity_per_store]},
      {type: along a scale..., value: !!null '', background_color: "#5A30C2", font_color: !!null '',
        color_application: {collection_id: f14810d2-98d7-42df-82d0-bc185a074e42, custom: {
            id: 4235bfed-58e1-1626-48da-a6a40492da29, label: Custom, type: continuous,
            stops: [{color: "#fff", offset: 0}, {color: "#9d81e6", offset: 50}, {
                color: "#5930c2", offset: 100}]}, options: {steps: 5}}, bold: false,
        italic: false, strikethrough: false, fields: [transactions.number_of_transactions_per_store]}]
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
    stacking: normal
    legend_position: center
    series_types: {}
    point_style: circle
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    reference_lines: [{reference_type: range, margin_top: deviation, margin_value: mean,
        margin_bottom: deviation, label_position: right, color: "#588eff", line_value: '10',
        range_start: "-10", range_end: '10', label: Cold}, {reference_type: range,
        line_value: mean, margin_top: deviation, margin_value: mean, margin_bottom: deviation,
        label_position: right, color: "#f0c157", range_start: '10', range_end: '20',
        label: Warm}, {reference_type: range, line_value: mean, margin_top: deviation,
        margin_value: mean, margin_bottom: deviation, label_position: right, color: "#ed5432",
        range_start: '20', range_end: '60', label: Hot}]
    show_null_points: true
    interpolation: linear
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    transpose: false
    truncate_text: true
    size_to_fit: true
    series_cell_visualizations:
      focus_store_sales_change:
        is_active: false
      other_stores_sales_change:
        is_active: true
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
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
    map_marker_type: circle
    map_marker_icon_name: default
    map_marker_radius_mode: proportional_value
    map_marker_units: pixels
    map_marker_radius_min: 3
    map_marker_radius_max: 20
    map_marker_proportional_scale_type: linear
    map_marker_color_mode: value
    show_legend: true
    map_value_colors: ["#aaa", "#5930c2"]
    quantize_map_value_colors: false
    reverse_map_value_colors: false
    color_range: ["#5A30C2", "#9d81e6", "#2D2442", "#42248F", "#1F1142"]
    color_by: root
    hidden_fields: []
    defaults_version: 1
    listen:
      Date: transactions.transaction_week
      Store: stores.store_for_comparison
    row: 35
    col: 0
    width: 24
    height: 10
  - title: How well am I gaining key customer segments vs peer stores?
    name: How well am I gaining key customer segments vs peer stores?
    model: retail_block_model
    explore: transactions
    type: looker_bar
    fields: [stores.store_comparison_vs_tier, transactions.number_of_transactions_change,
      customer_clustering_prediction.customer_segment, transactions.number_of_customers_change]
    pivots: [stores.store_comparison_vs_tier]
    filters:
      transactions.transaction_date: 2 years
      customer_clustering_prediction.customer_segment: "-NULL"
      transactions.comparison_type: year
    sorts: [stores.store_comparison_vs_tier 0, customer_clustering_prediction.customer_segment]
    limit: 500
    column_limit: 50
    color_application:
      collection_id: f14810d2-98d7-42df-82d0-bc185a074e42
      custom:
        id: 31e42998-49be-9a52-785f-aa0045688ee9
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
    series_types: {}
    point_style: circle
    series_colors: {}
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    reference_lines: []
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    show_row_numbers: true
    truncate_column_names: false
    hide_totals: false
    hide_row_totals: false
    table_theme: white
    enable_conditional_formatting: true
    conditional_formatting: [{type: along a scale..., value: !!null '', background_color: "#5A30C2",
        font_color: !!null '', color_application: {collection_id: retailer-scheme,
          palette_id: retailer-scheme-sequential-0}, bold: false, italic: false, strikethrough: false,
        fields: []}, {type: along a scale..., value: !!null '', background_color: "#5A30C2",
        font_color: !!null '', color_application: {collection_id: retailer-scheme,
          palette_id: retailer-scheme-sequential-0}, bold: false, italic: false, strikethrough: false,
        fields: []}]
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    show_null_points: true
    interpolation: linear
    transpose: false
    truncate_text: true
    size_to_fit: true
    series_cell_visualizations:
      focus_store_sales_change:
        is_active: false
      other_stores_sales_change:
        is_active: true
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
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
    map_marker_type: circle
    map_marker_icon_name: default
    map_marker_radius_mode: proportional_value
    map_marker_units: pixels
    map_marker_radius_min: 3
    map_marker_radius_max: 20
    map_marker_proportional_scale_type: linear
    map_marker_color_mode: value
    show_legend: true
    map_value_colors: ["#aaa", "#5930c2"]
    quantize_map_value_colors: false
    reverse_map_value_colors: false
    color_range: ["#5A30C2", "#9d81e6", "#2D2442", "#42248F", "#1F1142"]
    color_by: root
    hidden_fields: [transactions.number_of_transactions_change]
    note_state: expanded
    note_display: below
    note_text: ''
    listen:
      Date: transactions.date_comparison_filter
      Store: stores.store_for_comparison
    row: 49
    col: 12
    width: 12
    height: 9
  - name: "<span class='fa fa-boxes'> Inventory Tracking</span>"
    type: text
    title_text: "<span class='fa fa-boxes'> Inventory Tracking</span>"
    subtitle_text: <font color="#5b30c2">Where are the opportunities to optimise my
      inventory?</font>
    body_text: |-
      <center><strong>Recommended Action ?</strong>
      Check which products are over/under stocked and make/save money accordingly. Compare to products that are selling better in peer stores, and order them in or drill into their item dynamics to see how to bundle them.</center>
    row: 23
    col: 0
    width: 24
    height: 4
  - title: Total Value of Missing Stock
    name: Total Value of Missing Stock
    model: retail_block_model
    explore: stock_forecasting_explore_base
    type: single_value
    fields: [stock_forecasting_explore_base.total_quantity, stock_forecasting_prediction.forecasted_quantity,
      stock_forecasting_explore_base.stock_difference, stock_forecasting_explore_base.stock_difference_value,
      stock_forecasting_explore_base.product_name]
    filters:
      stock_forecasting_explore_base.stock_difference_value: ">0"
    sorts: [stock_forecasting_explore_base.stock_difference_value desc]
    limit: 500
    dynamic_fields: [{table_calculation: missing_stock_value, label: Missing Stock
          Value, expression: 'sum(${stock_forecasting_explore_base.stock_difference_value})',
        value_format: !!null '', value_format_name: usd_0, _kind_hint: measure, _type_hint: number}]
    query_timezone: America/Los_Angeles
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: true
    conditional_formatting: [{type: greater than, value: 0, background_color: '',
        font_color: "#86c780", color_application: {collection_id: retailer-scheme,
          palette_id: retailer-scheme-sequential-0}, bold: false, italic: false, strikethrough: false,
        fields: !!null ''}]
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
      stock_forecasting_explore_base.total_quantity:
        is_active: false
      stock_forecasting_explore_base.stock_difference_value:
        is_active: true
        palette:
          palette_id: retailer-scheme-diverging-0
          collection_id: retailer-scheme
    table_theme: white
    limit_displayed_rows: false
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
    series_types: {}
    hidden_fields: [stock_forecasting_explore_base.product_name, stock_forecasting_explore_base.stock_difference_value,
      stock_forecasting_explore_base.total_quantity, stock_forecasting_prediction.forecasted_quantity,
      stock_forecasting_explore_base.stock_difference]
    listen:
      Date: stock_forecasting_explore_base.transaction_week_filter
      Store: stock_forecasting_explore_base.store_name
    row: 27
    col: 16
    width: 8
    height: 4
  - title: Total Value of Overstock
    name: Total Value of Overstock
    model: retail_block_model
    explore: stock_forecasting_explore_base
    type: single_value
    fields: [stock_forecasting_explore_base.total_quantity, stock_forecasting_prediction.forecasted_quantity,
      stock_forecasting_explore_base.stock_difference, stock_forecasting_explore_base.stock_difference_value,
      stock_forecasting_explore_base.product_name]
    filters:
      stock_forecasting_explore_base.stock_difference_value: "<0"
    sorts: [stock_forecasting_explore_base.stock_difference_value desc]
    limit: 500
    dynamic_fields: [{table_calculation: missing_stock_value, label: Missing Stock
          Value, expression: 'sum(${stock_forecasting_explore_base.stock_difference_value})',
        value_format: !!null '', value_format_name: usd_0, _kind_hint: measure, _type_hint: number}]
    query_timezone: America/Los_Angeles
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: true
    conditional_formatting: [{type: less than, value: 0, background_color: '', font_color: "#a61610",
        color_application: {collection_id: retailer-scheme, palette_id: retailer-scheme-sequential-0},
        bold: false, italic: false, strikethrough: false, fields: !!null ''}]
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
      stock_forecasting_explore_base.total_quantity:
        is_active: false
      stock_forecasting_explore_base.stock_difference_value:
        is_active: true
        palette:
          palette_id: retailer-scheme-diverging-0
          collection_id: retailer-scheme
    table_theme: white
    limit_displayed_rows: false
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
    series_types: {}
    hidden_fields: [stock_forecasting_explore_base.product_name, stock_forecasting_explore_base.stock_difference_value,
      stock_forecasting_explore_base.total_quantity, stock_forecasting_prediction.forecasted_quantity,
      stock_forecasting_explore_base.stock_difference]
    listen:
      Date: stock_forecasting_explore_base.transaction_week_filter
      Store: stock_forecasting_explore_base.store_name
    row: 31
    col: 16
    width: 8
    height: 4
  - title: Weather Trend vs Sales Trend - Peer Stores
    name: Weather Trend vs Sales Trend - Peer Stores
    model: retail_block_model
    explore: transactions
    type: looker_line
    fields: [store_weather.average_max_temparature, transactions.transaction_date,
      transactions__line_items.total_sales_per_store]
    fill_fields: [transactions.transaction_date]
    filters:
      transactions.transaction_date: 14 days
      stores.store_comparison_vs_tier: 2-%
    sorts: [transactions.transaction_date desc]
    limit: 500
    column_limit: 1
    dynamic_fields: [{table_calculation: focus_store_transaction_count_change, label: Focus
          Store Transaction Count Change (%), expression: 'if(contains(${stores.store_comparison_vs_stores_in_tier_with_weather},"1-
          "),${transactions.number_of_transactions_change},null)', value_format: !!null '',
        value_format_name: percent_1, _kind_hint: measure, _type_hint: number, is_disabled: true},
      {table_calculation: other_stores_transaction_count_change, label: Other Stores
          Transaction Count Change (%), expression: 'if(contains(${stores.store_comparison_vs_stores_in_tier_with_weather},"1-
          "),null,${transactions.number_of_transactions_change})', value_format: !!null '',
        value_format_name: percent_1, _kind_hint: measure, _type_hint: number, is_disabled: true}]
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    y_axes: [{label: '', orientation: left, series: [{axisId: store_weather.average_max_temparature,
            id: store_weather.average_max_temparature, name: Average Max Temparature}],
        showLabels: true, showValues: true, unpinAxis: false, tickDensity: default,
        type: linear}, {label: '', orientation: right, series: [{axisId: transactions__line_items.total_sales_per_store,
            id: transactions__line_items.total_sales_per_store, name: Total Sales
              per Store}], showLabels: true, showValues: true, unpinAxis: false, tickDensity: default,
        type: linear}]
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
    hidden_series: []
    legend_position: center
    series_types: {}
    point_style: circle
    series_colors:
      1- Los Angeles - transactions__line_items.total_sales_per_store: "#1F1142"
      2- Rest of Stores in Tier - store_weather.average_max_temparature: "#5A30C2"
      2- Rest of Stores in Tier - transactions__line_items.total_sales_per_store: "#1F1142"
      store_weather.average_max_temparature: "#9d81e6"
      transactions__line_items.total_sales_per_store: "#1F1142"
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    reference_lines: [{reference_type: range, margin_top: deviation, margin_value: mean,
        margin_bottom: deviation, label_position: right, color: "#588eff", line_value: '10',
        range_start: "-10", range_end: '10', label: Cold}, {reference_type: range,
        line_value: mean, margin_top: deviation, margin_value: mean, margin_bottom: deviation,
        label_position: right, color: "#f0c157", range_start: '10', range_end: '20',
        label: Warm}, {reference_type: range, line_value: mean, margin_top: deviation,
        margin_value: mean, margin_bottom: deviation, label_position: right, color: "#ed5432",
        range_start: '20', range_end: '60', label: Hot}]
    show_null_points: false
    interpolation: linear
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    show_row_numbers: true
    transpose: false
    truncate_text: true
    hide_totals: false
    hide_row_totals: false
    size_to_fit: true
    series_cell_visualizations:
      focus_store_sales_change:
        is_active: false
      other_stores_sales_change:
        is_active: true
    table_theme: white
    enable_conditional_formatting: false
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
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
    map_marker_type: circle
    map_marker_icon_name: default
    map_marker_radius_mode: proportional_value
    map_marker_units: pixels
    map_marker_radius_min: 3
    map_marker_radius_max: 20
    map_marker_proportional_scale_type: linear
    map_marker_color_mode: value
    show_legend: true
    map_value_colors: ["#aaa", "#5930c2"]
    quantize_map_value_colors: false
    reverse_map_value_colors: false
    color_range: ["#5A30C2", "#9d81e6", "#2D2442", "#42248F", "#1F1142"]
    color_by: root
    hidden_fields: []
    listen:
      Store: stores.store_for_comparison
    row: 16
    col: 12
    width: 12
    height: 7
  - title: Main Over-/Under- Stocked Products
    name: Main Over-/Under- Stocked Products
    model: retail_block_model
    explore: stock_forecasting_explore_base
    type: looker_grid
    fields: [stock_forecasting_explore_base.product_name, stock_forecasting_explore_base.total_quantity,
      stock_forecasting_prediction.forecasted_quantity, stock_forecasting_explore_base.stock_difference,
      stock_forecasting_explore_base.stock_difference_value]
    filters:
      stock_forecasting_explore_base.stock_difference: not 0
      stock_forecasting_explore_base.stock_difference_value: ">0,<-200"
    sorts: [stock_forecasting_explore_base.stock_difference_value desc]
    limit: 500
    column_limit: 50
    show_view_names: false
    show_row_numbers: true
    transpose: false
    truncate_text: true
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
    show_totals: true
    show_row_totals: true
    series_cell_visualizations:
      stock_forecasting_explore_base.total_quantity:
        is_active: false
      stock_forecasting_explore_base.stock_difference_value:
        is_active: true
        palette:
          palette_id: 0ab20095-1901-c8ba-05e9-122c506bc899
          collection_id: f14810d2-98d7-42df-82d0-bc185a074e42
          custom_colors:
          - "#a8282e"
          - "#ffffff"
          - "#5930c2"
    series_types: {}
    defaults_version: 1
    listen:
      Date: stock_forecasting_explore_base.transaction_week_filter
      Store: stock_forecasting_explore_base.store_name
    row: 27
    col: 0
    width: 16
    height: 8
  filters:
  - name: Date
    title: Date
    type: date_filter
    default_value: 7 days
    allow_multiple_values: true
    required: false
  - name: Store
    title: Store
    type: field_filter
    default_value: Los Angeles
    allow_multiple_values: true
    required: false
    model: retail_block_model
    explore: transactions
    listens_to_filters: []
    field: stores.name
