explore: looker_group_tag {
  tags: ["group:customized_group", "customized_tag", "customized tag with whitespace"]
}

explore: looker_group_tag_has_trimmed_whitespace {
  tags: ["group: customized_group", "customized_tag", "customized tag with whitespace"]
}

explore: looker_group_tag_has_replaced_whitespace {
  tags: ["group: customized group", "customized_tag", "customized tag with whitespace"]
}