view: weather_raw {
  derived_table: {
    datagroup_trigger: daily
    partition_keys: ["date"]
    # requires ID, latitude, longitude columns in stores table
      # TO DO: update DATE_ADD(,+1 YEAR) with 2020 table once available in BQ public dataset
    sql: SELECT id,date,element,value,mflag,qflag,sflag,time FROM `bigquery-public-data.ghcn_d.ghcnd_202*`
        UNION ALL SELECT id,date,element,value,mflag,qflag,sflag,time FROM `bigquery-public-data.ghcn_d.ghcnd_2019`
        UNION ALL SELECT id,date,element,value,mflag,qflag,sflag,time FROM `bigquery-public-data.ghcn_d.ghcnd_2018`
        UNION ALL SELECT id,date,element,value,mflag,qflag,sflag,time FROM `bigquery-public-data.ghcn_d.ghcnd_2017`
        UNION ALL SELECT id,date,element,value,mflag,qflag,sflag,time FROM `bigquery-public-data.ghcn_d.ghcnd_2016` ;;
  }
}

view: weather_pivoted {
  derived_table: {
    datagroup_trigger: daily
    partition_keys: ["date"]
    # requires ID, latitude, longitude columns in stores table
      # TO DO: update DATE_ADD(,+1 YEAR) with 2020 table once available in BQ public dataset
    sql: SELECT date,id
        ,AVG(CASE WHEN element="TMAX" THEN value ELSE NULL END) AS TMAX
        ,AVG(CASE WHEN element="WESD" THEN value ELSE NULL END) AS WESD
        ,AVG(CASE WHEN element="AWND" THEN value ELSE NULL END) AS AWND
        ,AVG(CASE WHEN element="WDMV" THEN value ELSE NULL END) AS WDMV
        ,AVG(CASE WHEN element="THIC" THEN value ELSE NULL END) AS THIC
        ,AVG(CASE WHEN element="SX51" THEN value ELSE NULL END) AS SX51
        ,AVG(CASE WHEN element="TAVG" THEN value ELSE NULL END) AS TAVG
        ,AVG(CASE WHEN element="TSUN" THEN value ELSE NULL END) AS TSUN
        ,AVG(CASE WHEN element="DAPR" THEN value ELSE NULL END) AS DAPR
        ,AVG(CASE WHEN element="WDF5" THEN value ELSE NULL END) AS WDF5
        ,AVG(CASE WHEN element="WT04" THEN value ELSE NULL END) AS WT04
        ,AVG(CASE WHEN element="MDSF" THEN value ELSE NULL END) AS MDSF
        ,AVG(CASE WHEN element="SNWD" THEN value ELSE NULL END) AS SNWD
        ,AVG(CASE WHEN element="MXPN" THEN value ELSE NULL END) AS MXPN
        ,AVG(CASE WHEN element="WESF" THEN value ELSE NULL END) AS WESF
        ,AVG(CASE WHEN element="MDTN" THEN value ELSE NULL END) AS MDTN
        ,AVG(CASE WHEN element="SX36" THEN value ELSE NULL END) AS SX36
        ,AVG(CASE WHEN element="DASF" THEN value ELSE NULL END) AS DASF
        ,AVG(CASE WHEN element="TMIN" THEN value ELSE NULL END) AS TMIN
        ,AVG(CASE WHEN element="TOBS" THEN value ELSE NULL END) AS TOBS
        ,AVG(CASE WHEN element="WSFG" THEN value ELSE NULL END) AS WSFG
        ,AVG(CASE WHEN element="MNPN" THEN value ELSE NULL END) AS MNPN
        ,AVG(CASE WHEN element="SN32" THEN value ELSE NULL END) AS SN32
        ,AVG(CASE WHEN element="SX31" THEN value ELSE NULL END) AS SX31
        ,AVG(CASE WHEN element="SX33" THEN value ELSE NULL END) AS SX33
        ,AVG(CASE WHEN element="WSF5" THEN value ELSE NULL END) AS WSF5
        ,AVG(CASE WHEN element="WDF2" THEN value ELSE NULL END) AS WDF2
        ,AVG(CASE WHEN element="SN55" THEN value ELSE NULL END) AS SN55
        ,AVG(CASE WHEN element="SN35" THEN value ELSE NULL END) AS SN35
        ,AVG(CASE WHEN element="AWDR" THEN value ELSE NULL END) AS AWDR
        ,AVG(CASE WHEN element="DATN" THEN value ELSE NULL END) AS DATN
        ,AVG(CASE WHEN element="WSFI" THEN value ELSE NULL END) AS WSFI
        ,AVG(CASE WHEN element="SN36" THEN value ELSE NULL END) AS SN36
        ,AVG(CASE WHEN element="MDTX" THEN value ELSE NULL END) AS MDTX
        ,AVG(CASE WHEN element="WT01" THEN value ELSE NULL END) AS WT01
        ,AVG(CASE WHEN element="WT11" THEN value ELSE NULL END) AS WT11
        ,AVG(CASE WHEN element="SN57" THEN value ELSE NULL END) AS SN57
        ,AVG(CASE WHEN element="WDFG" THEN value ELSE NULL END) AS WDFG
        ,AVG(CASE WHEN element="SN56" THEN value ELSE NULL END) AS SN56
        ,AVG(CASE WHEN element="SX56" THEN value ELSE NULL END) AS SX56
        ,AVG(CASE WHEN element="WT02" THEN value ELSE NULL END) AS WT02
        ,AVG(CASE WHEN element="WT09" THEN value ELSE NULL END) AS WT09
        ,AVG(CASE WHEN element="WT10" THEN value ELSE NULL END) AS WT10
        ,AVG(CASE WHEN element="WT16" THEN value ELSE NULL END) AS WT16
        ,AVG(CASE WHEN element="PRCP" THEN value ELSE NULL END) AS PRCP
        ,AVG(CASE WHEN element="MDPR" THEN value ELSE NULL END) AS MDPR
        ,AVG(CASE WHEN element="SX52" THEN value ELSE NULL END) AS SX52
        ,AVG(CASE WHEN element="SX32" THEN value ELSE NULL END) AS SX32
        ,AVG(CASE WHEN element="SN53" THEN value ELSE NULL END) AS SN53
        ,AVG(CASE WHEN element="SX55" THEN value ELSE NULL END) AS SX55
        ,AVG(CASE WHEN element="WT03" THEN value ELSE NULL END) AS WT03
        ,AVG(CASE WHEN element="WT05" THEN value ELSE NULL END) AS WT05
        ,AVG(CASE WHEN element="WT17" THEN value ELSE NULL END) AS WT17
        ,AVG(CASE WHEN element="EVAP" THEN value ELSE NULL END) AS EVAP
        ,AVG(CASE WHEN element="SN52" THEN value ELSE NULL END) AS SN52
        ,AVG(CASE WHEN element="SNOW" THEN value ELSE NULL END) AS SNOW
        ,AVG(CASE WHEN element="SX53" THEN value ELSE NULL END) AS SX53
        ,AVG(CASE WHEN element="SN51" THEN value ELSE NULL END) AS SN51
        ,AVG(CASE WHEN element="PGTM" THEN value ELSE NULL END) AS PGTM
        ,AVG(CASE WHEN element="WSF2" THEN value ELSE NULL END) AS WSF2
        ,AVG(CASE WHEN element="WT06" THEN value ELSE NULL END) AS WT06
        ,AVG(CASE WHEN element="WT08" THEN value ELSE NULL END) AS WT08
        ,AVG(CASE WHEN element="WT07" THEN value ELSE NULL END) AS WT07
        ,AVG(CASE WHEN element="SX57" THEN value ELSE NULL END) AS SX57
        ,AVG(CASE WHEN element="WT22" THEN value ELSE NULL END) AS WT22
        ,AVG(CASE WHEN element="WT15" THEN value ELSE NULL END) AS WT15
        ,AVG(CASE WHEN element="SN31" THEN value ELSE NULL END) AS SN31
        ,AVG(CASE WHEN element="SN33" THEN value ELSE NULL END) AS SN33
        ,AVG(CASE WHEN element="PSUN" THEN value ELSE NULL END) AS PSUN
        ,AVG(CASE WHEN element="DATX" THEN value ELSE NULL END) AS DATX
        ,AVG(CASE WHEN element="DWPR" THEN value ELSE NULL END) AS DWPR
        ,AVG(CASE WHEN element="SX35" THEN value ELSE NULL END) AS SX35
        ,AVG(CASE WHEN element="WT18" THEN value ELSE NULL END) AS WT18
        FROM ${weather_raw.SQL_TABLE_NAME}
        GROUP BY date,id ;;
    }
  }

view: distances {
  derived_table: {
    datagroup_trigger: daily
    sql: SELECT stores.id as store_id
        ,stations.id AS station_id
        ,ST_DISTANCE(ST_GEOGPOINT(stores.longitude,stores.latitude),ST_GEOGPOINT(stations.longitude,stations.latitude)) as dist
        FROM ${stores.SQL_TABLE_NAME} stores
        CROSS JOIN `bigquery-public-data.ghcn_d.ghcnd_stations` stations ;;
  }
}

view: store_weather {
  label: "Store Weather ⛅"
  derived_table: {
    datagroup_trigger: daily
    partition_keys: ["date"]
    cluster_keys: ["store_id"]
    # requires ID, latitude, longitude columns in stores table
      # TO DO: update DATE_ADD(,+1 YEAR) with 2020 table once available in BQ public dataset
    sql: SELECT distances.store_id
          ,weather_pivoted.date
          ,AVG(distances.dist/1000) AS average_distance_to_weather_stations_km
          ,AVG(TMAX) AS TMAX
          ,AVG(WESD) AS WESD
          ,AVG(AWND) AS AWND
          ,AVG(WDMV) AS WDMV
          ,AVG(THIC) AS THIC
          ,AVG(SX51) AS SX51
          ,AVG(TAVG) AS TAVG
          ,AVG(TSUN) AS TSUN
          ,AVG(DAPR) AS DAPR
          ,AVG(WDF5) AS WDF5
          ,AVG(WT04) AS WT04
          ,AVG(MDSF) AS MDSF
          ,AVG(SNWD) AS SNWD
          ,AVG(MXPN) AS MXPN
          ,AVG(WESF) AS WESF
          ,AVG(MDTN) AS MDTN
          ,AVG(SX36) AS SX36
          ,AVG(DASF) AS DASF
          ,AVG(TMIN) AS TMIN
          ,AVG(TOBS) AS TOBS
          ,AVG(WSFG) AS WSFG
          ,AVG(MNPN) AS MNPN
          ,AVG(SN32) AS SN32
          ,AVG(SX31) AS SX31
          ,AVG(SX33) AS SX33
          ,AVG(WSF5) AS WSF5
          ,AVG(WDF2) AS WDF2
          ,AVG(SN55) AS SN55
          ,AVG(SN35) AS SN35
          ,AVG(AWDR) AS AWDR
          ,AVG(DATN) AS DATN
          ,AVG(WSFI) AS WSFI
          ,AVG(SN36) AS SN36
          ,AVG(MDTX) AS MDTX
          ,AVG(WT01) AS WT01
          ,AVG(WT11) AS WT11
          ,AVG(SN57) AS SN57
          ,AVG(WDFG) AS WDFG
          ,AVG(SN56) AS SN56
          ,AVG(SX56) AS SX56
          ,AVG(WT02) AS WT02
          ,AVG(WT09) AS WT09
          ,AVG(WT10) AS WT10
          ,AVG(WT16) AS WT16
          ,AVG(PRCP) AS PRCP
          ,AVG(MDPR) AS MDPR
          ,AVG(SX52) AS SX52
          ,AVG(SX32) AS SX32
          ,AVG(SN53) AS SN53
          ,AVG(SX55) AS SX55
          ,AVG(WT03) AS WT03
          ,AVG(WT05) AS WT05
          ,AVG(WT17) AS WT17
          ,AVG(EVAP) AS EVAP
          ,AVG(SN52) AS SN52
          ,AVG(SNOW) AS SNOW
          ,AVG(SX53) AS SX53
          ,AVG(SN51) AS SN51
          ,AVG(PGTM) AS PGTM
          ,AVG(WSF2) AS WSF2
          ,AVG(WT06) AS WT06
          ,AVG(WT08) AS WT08
          ,AVG(WT07) AS WT07
          ,AVG(SX57) AS SX57
          ,AVG(WT22) AS WT22
          ,AVG(WT15) AS WT15
          ,AVG(SN31) AS SN31
          ,AVG(SN33) AS SN33
          ,AVG(PSUN) AS PSUN
          ,AVG(DATX) AS DATX
          ,AVG(DWPR) AS DWPR
          ,AVG(SX35) AS SX35
          ,AVG(WT18) AS WT18
        FROM ${distances.SQL_TABLE_NAME} distances
        JOIN ${weather_pivoted.SQL_TABLE_NAME} weather_pivoted
          ON distances.station_id = weather_pivoted.id
        WHERE distances.dist < 30000
        GROUP BY 1,2;;
  }

  dimension: awdr {
    hidden: yes
    type: number
    sql: ${TABLE}.AWDR ;;
  }

  dimension: awnd {
    hidden: yes
    type: number
    sql: ${TABLE}.AWND ;;
  }

  dimension: dapr {
    hidden: yes
    type: number
    sql: ${TABLE}.DAPR ;;
  }

  dimension: dasf {
    hidden: yes
    type: number
    sql: ${TABLE}.DASF ;;
  }

  dimension_group: weather {
    hidden: yes
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
    sql: ${TABLE}.date ;;
  }

  dimension: datn {
    hidden: yes
    type: number
    sql: ${TABLE}.DATN ;;
  }

  dimension: datx {
    hidden: yes
    type: number
    sql: ${TABLE}.DATX ;;
  }

  dimension: average_distance_to_weather_stations_km {
    hidden: yes
    type: number
    sql: ${TABLE}.average_distance_to_weather_stations_km ;;
  }

  dimension: dwpr {
    hidden: yes
    type: number
    sql: ${TABLE}.DWPR ;;
  }

  dimension: evap {
    hidden: yes
    type: number
    sql: ${TABLE}.EVAP ;;
  }

  dimension: mdpr {
    hidden: yes
    type: number
    sql: ${TABLE}.MDPR ;;
  }

  dimension: mdsf {
    hidden: yes
    type: number
    sql: ${TABLE}.MDSF ;;
  }

  dimension: mdtn {
    hidden: yes
    type: number
    sql: ${TABLE}.MDTN ;;
  }

  dimension: mdtx {
    hidden: yes
    type: number
    sql: ${TABLE}.MDTX ;;
  }

  dimension: mnpn {
    hidden: yes
    type: number
    sql: ${TABLE}.MNPN ;;
  }

  dimension: mxpn {
    hidden: yes
    type: number
    sql: ${TABLE}.MXPN ;;
  }

  dimension: pgtm {
    hidden: yes
    type: number
    sql: ${TABLE}.PGTM ;;
  }

  dimension: prcp {
    label: "Precipitation (mm)"
    type: number
    sql: ${TABLE}.PRCP/10.0 ;;
  }

  dimension: psun {
    hidden: yes # not populated
    label: "Percent of Day Sunny (%)"
    value_format_name: percent_1
    type: number
    sql: ${TABLE}.PSUN ;;
  }

  dimension: sn31 {
    hidden: yes
    type: number
    sql: ${TABLE}.SN31 ;;
  }

  dimension: sn32 {
    hidden: yes
    type: number
    sql: ${TABLE}.SN32 ;;
  }

  dimension: sn33 {
    hidden: yes
    type: number
    sql: ${TABLE}.SN33 ;;
  }

  dimension: sn35 {
    hidden: yes
    type: number
    sql: ${TABLE}.SN35 ;;
  }

  dimension: sn36 {
    hidden: yes
    type: number
    sql: ${TABLE}.SN36 ;;
  }

  dimension: sn51 {
    hidden: yes
    type: number
    sql: ${TABLE}.SN51 ;;
  }

  dimension: sn52 {
    hidden: yes
    type: number
    sql: ${TABLE}.SN52 ;;
  }

  dimension: sn53 {
    hidden: yes
    type: number
    sql: ${TABLE}.SN53 ;;
  }

  dimension: sn55 {
    hidden: yes
    type: number
    sql: ${TABLE}.SN55 ;;
  }

  dimension: sn56 {
    hidden: yes
    type: number
    sql: ${TABLE}.SN56 ;;
  }

  dimension: sn57 {
    hidden: yes
    type: number
    sql: ${TABLE}.SN57 ;;
  }

  dimension: snow {
    label: "Snowfall (mm)"
    type: number
    sql: ${TABLE}.SNOW ;;
  }

  dimension: snwd {
    label: "Snow Depth (mm)"
    type: number
    sql: ${TABLE}.SNWD ;;
  }

  dimension: store_id {
    hidden: yes
    type: number
    sql: ${TABLE}.store_id ;;
  }

  dimension: sx31 {
    hidden: yes
    type: number
    sql: ${TABLE}.SX31 ;;
  }

  dimension: sx32 {
    hidden: yes
    type: number
    sql: ${TABLE}.SX32 ;;
  }

  dimension: sx33 {
    hidden: yes
    type: number
    sql: ${TABLE}.SX33 ;;
  }

  dimension: sx35 {
    hidden: yes
    type: number
    sql: ${TABLE}.SX35 ;;
  }

  dimension: sx36 {
    hidden: yes
    type: number
    sql: ${TABLE}.SX36 ;;
  }

  dimension: sx51 {
    hidden: yes
    type: number
    sql: ${TABLE}.SX51 ;;
  }

  dimension: sx52 {
    hidden: yes
    type: number
    sql: ${TABLE}.SX52 ;;
  }

  dimension: sx53 {
    hidden: yes
    type: number
    sql: ${TABLE}.SX53 ;;
  }

  dimension: sx55 {
    hidden: yes
    type: number
    sql: ${TABLE}.SX55 ;;
  }

  dimension: sx56 {
    hidden: yes
    type: number
    sql: ${TABLE}.SX56 ;;
  }

  dimension: sx57 {
    hidden: yes
    type: number
    sql: ${TABLE}.SX57 ;;
  }

  dimension: tavg {
    hidden: yes
    type: number
    sql: ${TABLE}.TAVG ;;
  }

  dimension: thic {
    hidden: yes
    type: number
    sql: ${TABLE}.THIC ;;
  }

  dimension: tmax {
    label: "Max Temperature (°C)"
    type: number
    sql: ${TABLE}.TMAX/10.0 ;;
  }

  dimension: tmin {
    label: "Min Temperature (°C)"
    type: number
    sql: ${TABLE}.TMIN/10.0 ;;
  }

  dimension: tobs {
    hidden: yes
    type: number
    sql: ${TABLE}.TOBS ;;
  }

  dimension: tsun {
    hidden: yes
    type: number
    sql: ${TABLE}.TSUN ;;
  }

  dimension: wdf2 {
    hidden: yes
    type: number
    sql: ${TABLE}.WDF2 ;;
  }

  dimension: wdf5 {
    hidden: yes
    type: number
    sql: ${TABLE}.WDF5 ;;
  }

  dimension: wdfg {
    hidden: yes
    type: number
    sql: ${TABLE}.WDFG ;;
  }

  dimension: wdmv {
    hidden: yes
    type: number
    sql: ${TABLE}.WDMV ;;
  }

  dimension: wesd {
    hidden: yes
    type: number
    sql: ${TABLE}.WESD ;;
  }

  dimension: wesf {
    hidden: yes
    type: number
    sql: ${TABLE}.WESF ;;
  }

  dimension: wsf2 {
    hidden: yes
    type: number
    sql: ${TABLE}.WSF2 ;;
  }

  dimension: wsf5 {
    hidden: yes
    type: number
    sql: ${TABLE}.WSF5 ;;
  }

  dimension: wsfg {
    hidden: yes
    type: number
    sql: ${TABLE}.WSFG ;;
  }

  dimension: wsfi {
    hidden: yes
    type: number
    sql: ${TABLE}.WSFI ;;
  }

  dimension: wt01 {
    hidden: yes
    type: number
    sql: ${TABLE}.WT01 ;;
  }

  dimension: wt02 {
    hidden: yes
    type: number
    sql: ${TABLE}.WT02 ;;
  }

  dimension: wt03 {
    hidden: yes
    type: number
    sql: ${TABLE}.WT03 ;;
  }

  dimension: wt04 {
    hidden: yes
    type: number
    sql: ${TABLE}.WT04 ;;
  }

  dimension: wt05 {
    hidden: yes
    type: number
    sql: ${TABLE}.WT05 ;;
  }

  dimension: wt06 {
    hidden: yes
    type: number
    sql: ${TABLE}.WT06 ;;
  }

  dimension: wt07 {
    hidden: yes
    type: number
    sql: ${TABLE}.WT07 ;;
  }

  dimension: wt08 {
    hidden: yes
    type: number
    sql: ${TABLE}.WT08 ;;
  }

  dimension: wt09 {
    hidden: yes
    type: number
    sql: ${TABLE}.WT09 ;;
  }

  dimension: wt10 {
    hidden: yes
    type: number
    sql: ${TABLE}.WT10 ;;
  }

  dimension: wt11 {
    hidden: yes
    type: number
    sql: ${TABLE}.WT11 ;;
  }

  dimension: wt15 {
    hidden: yes
    type: number
    sql: ${TABLE}.WT15 ;;
  }

  dimension: wt16 {
    hidden: yes
    type: number
    sql: ${TABLE}.WT16 ;;
  }

  dimension: wt17 {
    hidden: yes
    type: number
    sql: ${TABLE}.WT17 ;;
  }

  dimension: wt18 {
    hidden: yes
    type: number
    sql: ${TABLE}.WT18 ;;
  }

  dimension: wt22 {
    hidden: yes
    type: number
    sql: ${TABLE}.WT22 ;;
  }

  ##### DERIVED DIMENSIONS #####

  dimension: pk {
    hidden: yes
    primary_key: yes
    type: string
    sql: CONCAT(CAST(${weather_date} AS STRING),'-',CAST(${store_id} AS STRING)) ;;
  }

  ##### MEASURES #####

  measure: average_max_temparature {
    type: average
    sql: ${tmax} ;;
    value_format: "#,##0.0 \" °C\""
  }

  measure: average_min_temparature {
    type: average
    sql: ${tmin} ;;
    value_format: "#,##0.0 \" °C\""
  }

  measure: average_daily_precipitation {
    type: average
    sql: ${prcp} ;;
    value_format: "#,##0.0 \" mm\""
  }
}
