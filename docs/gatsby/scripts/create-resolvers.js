const {
  parseHtml,
  parseMarkdown,
  toParseFive,
  parseToc
} = require("./parse-html");

const {
  getCurrentVersion,
  getAllBuildedVersions
} = require("./utils/get-version");

const { getSlug } = require("./utils/get-slug");

module.exports = ({ createResolvers }) => {
  const resolvers = {
    Query: {
      dagsterVersion: {
        type: "String",
        resolve() {
          return getCurrentVersion();
        }
      },
      allDagsterVersion: {
        type: "[String!]",
        resolve() {
          return getAllBuildedVersions();
        }
      }
    },
    SphinxPage: {
      body: {
        resolve(source) {
          try {
            return parseHtml(source.body, getCurrentVersion());
          } catch (err) {
            return source.body;
          }
        }
      },
      parsed: {
        resolve(source) {
          return toParseFive(source.body);
        }
      },
      tocParsed: {
        resolve(source) {
          return source.toc && parseToc(source.toc);
        }
      },
      markdown: {
        resolve(source) {
          try {
            const md = parseMarkdown(source.body, getCurrentVersion());
            return md.slice(0, 5000);
          } catch (err) {
            return source.body;
          }
        }
      },
      slug: {
        resolve(source) {
          return getSlug(source);
        }
      }
    }
  };

  createResolvers(resolvers);
};
