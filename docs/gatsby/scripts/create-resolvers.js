const { parseHtml, toParseFive } = require("./parse-html");
const { getCurrentVersion, getAllVersions } = require("./utils/get-version");

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
          return getAllVersions();
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
          return source.toc && toParseFive(source.toc);
        }
      }
    }
  };

  createResolvers(resolvers);
};
