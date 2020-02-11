module.exports = ({ actions }) => {
  const { createTypes } = actions;
  const typeDefs = `type SphinxPage implements Node {
      parsed: String
      tocParsed: String
      markdown: String
      slug: String
    }`;

  createTypes(typeDefs);
};
