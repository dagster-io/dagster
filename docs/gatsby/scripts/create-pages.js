const path = require("path");

const { getAllBuildedVersions } = require("./utils/get-version");
const ALL_VERSIONS = getAllBuildedVersions();

module.exports = async ({ graphql, actions }) => {
  const result = await graphql(`
    query SphinxPages {
      __typename
      allSphinxPage {
        edges {
          node {
            body
            parsed
            current_page_name
            title
            id
            tocParsed
            toc
            slug
            prev {
              title
              link
            }
            next {
              title
              link
            }
            parents {
              title
              link
            }
          }
        }
      }
    }
  `);
  result.data.allSphinxPage.edges.forEach(({ node }) => {
    if (node.slug) {
      ALL_VERSIONS.forEach(version => {
        actions.createPage({
          path: `${version}/${node.slug}`,
          component: path.resolve("./src/templates/SphinxPage/index.js"),
          context: {
            page: node
          }
        });
      });
    }
  });
};
