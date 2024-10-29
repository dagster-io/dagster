view: contracts_fact {
  sql_table_name: `ra-development.analytics.contracts_fact`
    ;;

  dimension: authorised_contract_signatory {
    type: string
    sql: ${TABLE}.authorised_contract_signatory ;;
  }

  dimension: company_pk {
    hidden: yes
    type: string
    sql: ${TABLE}.company_fk ;;
  }

  dimension: contact_email {
    hidden: yes
    type: string
    sql: ${TABLE}.contact_email ;;
  }

  dimension: contact_id {
    hidden: yes

    type: string
    sql: ${TABLE}.contact_id ;;
  }

  dimension: contact_name {
    type: string
    sql: ${TABLE}.contact_name ;;
  }

  dimension: contact_pk {
    hidden: yes

    type: string
    sql: ${TABLE}.contact_pk ;;
  }

  dimension: contact_title {
    type: string
    sql: ${TABLE}.contact_title ;;
  }

  dimension_group: contract {
    type: time
    timeframes: [date]
    sql: parse_timestamp('%m/%d/%Y %I:%M:%S %p %Z',replace(${TABLE}.contract_executed_ts,'BST','GMT')) ;;
  }

  dimension: contract_id {
    hidden: yes

    type: string
    sql: ${TABLE}.contract_id ;;
  }

  dimension: contract_name {
    label: "   Contract Name"
    type: string
    sql: ${TABLE}.contract_name ;;
  }

  dimension: contract_pk {
    hidden: yes

    type: string
    sql: ${TABLE}.contract_pk ;;
  }

  dimension: contract_status {
    type: string
    sql: ${TABLE}.contract_status ;;
  }

  dimension_group: contract_voided {
    type: time
    timeframes: [date]
    sql: parse_timestamp('%m/%d/%Y %I:%M:%S %p %Z',replace(${TABLE}.contract_voided_on_ts,'BST','GMT')) ;;
  }

  dimension: email_domain {
    hidden: yes

    type: string
    sql: ${TABLE}.email_domain ;;
  }

  dimension: is_completed {
    type: yesno
    sql: ${TABLE}.is_completed ;;
  }

  dimension: is_voided {
    type: yesno
    sql: ${TABLE}.is_voided ;;
  }

  dimension_group: last_modified {
     type: time
    timeframes: [date]
    sql: parse_timestamp('%m/%d/%Y %I:%M:%S %p %Z',replace(${TABLE}.last_modified_date,'BST','GMT'))  ;;
  }

  dimension_group: contract_sent {
   type: time
    timeframes: [date]
    sql: parse_timestamp('%m/%d/%Y %I:%M:%S %p %Z',replace(${TABLE}.sent_ts,'BST','GMT')) ;;
  }

  dimension: source {
    type: string
    sql: ${TABLE}.source ;;
  }

  dimension: total_completed_signatures {
    hidden: yes
    type: number
    sql: ${TABLE}.total_completed_signatures ;;
  }

  dimension: total_remaining_signatures {
    type: number
    sql: ${TABLE}.total_remaining_signatures ;;
  }

  dimension: pct_complete {
    type: number
    sql: 1-(${TABLE}.total_remaining_signatures/(${TABLE}.total_completed_signatures+${TABLE}.total_remaining_signatures)) ;;
  }

  measure: avg_pct_signatures_remaining {
    value_format_name: percent_0
    type: average
    sql: ${pct_complete} ;;
  }

  dimension: voided_reason {
    type: string
    sql: ${TABLE}.voided_reason ;;
  }


}
