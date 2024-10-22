VERIFICATION_QUERY = """
query VerificationQuery($environmentId: BigInt!) {
  environment(id: $environmentId) {
    __typename
  }
}
"""
