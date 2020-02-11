const R = require("ramda");

const pageQuery = `{
  pages: allSphinxPage(limit: 10000) {
    edges {
      node {
        objectID: id,
        title
        markdown
        slug
      }
    }
  }
}`;

const settings = {
  attributesToSnippet: [`markdown:20`]
};

const queries = [
  {
    settings,
    query: pageQuery,
    indexName: `Pages`,
    transformer: ({ data }) => {
      return data.pages.edges
        .filter(({ node }) => node.slug && !node.slug.startsWith("_modules"))
        .map(R.prop("node"));
    }
  },
  {
    settings,
    query: pageQuery,
    indexName: `Modules`,
    transformer: ({ data }) => {
      return data.pages.edges
        .filter(({ node }) => node.slug && node.slug.startsWith("_modules"))
        .map(R.prop("node"));
    }
  }
];

module.exports = queries;
