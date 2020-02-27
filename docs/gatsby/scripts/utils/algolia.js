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

// We are operating under an Algolia record size limit (currently 10KB). Before this changeset,
// we were just truncating records at 5000 chars. Now we chunk each document into 8000 char
// records with the same name -- Algolia dedupes based on the values of
// distinct/attributeForDistinct set on the index. A further improvement here would be to chunk at
// word boundaries.
const CHUNK_SIZE = 8000;
const recordChunker = (accumulator, currentValue) => {
  if (currentValue.markdown.length <= CHUNK_SIZE) {
    accumulator.push(currentValue);
    return accumulator;
  } else {
    let markdown = currentValue.markdown;
    const objectID = currentValue.objectID;
    let i = 0;
    while (markdown.length > 0) {
      let nextValue = {
        objectID: currentValue.objectID,
        title: currentValue.title,
        markdown: currentValue.markdown,
        slug: currentValue.slug
      };
      nextValue.markdown = markdown.slice(0, CHUNK_SIZE);
      nextValue.objectID = objectID + "_" + i.toString();
      i = i + 1;
      accumulator.push(nextValue);
      markdown = markdown.slice(CHUNK_SIZE);
    }
    return accumulator;
  }
};

const queries = [
  {
    settings,
    query: pageQuery,
    indexName: `Pages`,
    transformer: ({ data }) => {
      return data.pages.edges
        .filter(({ node }) => node.slug && !node.slug.startsWith("_modules"))
        .map(R.prop("node"))
        .reduce(recordChunker, []);
    }
  },
  {
    settings: {
      attributesToSnippet: [`markdown:20`],
      queryLanguages: ["en"],
      distinct: true,
      attributeForDistinct: "title"
    },
    query: pageQuery,
    indexName: `Modules`,
    transformer: ({ data }) => {
      return data.pages.edges
        .filter(({ node }) => node.slug && node.slug.startsWith("_modules"))
        .map(R.prop("node"))
        .reduce(recordChunker, []);
    }
  }
];

module.exports = queries;
