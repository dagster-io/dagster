module.exports = ({ actions }) => {
  const { createTypes } = actions
  const typeDefs = `type SphinxPage implements Node {
      parsed: String
      tocParsed: String
    }`

  createTypes(typeDefs)
}
