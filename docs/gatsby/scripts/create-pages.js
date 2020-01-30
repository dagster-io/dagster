const R = require("ramda");
const path = require("path");

const { getAllVersions } = require("./utils/get-version");
const ALL_VERSIONS = getAllVersions();

const getPath = pageName => {
  return pageName.endsWith("/index")
    ? pageName.replace("/index", "")
    : pageName;
};

const checkNodeBeforeCreatePage = node => {
  const pageName = node.current_page_name;
  if (!pageName) return;
  if (["genindex", "index", "py-modindex"].some(R.equals(pageName))) return;
  return Boolean(node.title);
};

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
          }
        }
      }
    }
  `);
  result.data.allSphinxPage.edges.forEach(({ node }) => {
    if (checkNodeBeforeCreatePage(node)) {
      const currpath = getPath(node.current_page_name).replace("sections/", "");
      ALL_VERSIONS.forEach(version => {
        actions.createPage({
          path: `${version}/${currpath}`,
          component: path.resolve("./src/templates/SphinxPage/index.js"),
          context: {
            page: node
          }
        });
      });
    }
  });
};
