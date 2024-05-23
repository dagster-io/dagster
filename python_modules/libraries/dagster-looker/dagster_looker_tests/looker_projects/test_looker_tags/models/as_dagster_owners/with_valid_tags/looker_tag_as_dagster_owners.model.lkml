explore: looker_owner_user_tag {
  tags: ["owner:owner@company.com"]
}

explore: looker_owner_user_tag_has_trimmed_whitespace {
  tags: ["owner: owner@company.com"]
}

explore: looker_owner_team_tag {
  tags: ["owner:team:customized_owner"]
}

explore: looker_owner_coerced_team_tag {
  tags: ["owner:customized_owner"]
}

explore: looker_owner_coerced_team_tag_has_replaced_whitespace {
  tags: ["owner: customized owner"]
}

explore: looker_owner_team_tag_has_trimmed_whitespace {
  tags: ["owner: team:customized_owner"]
}