require("dotenv").config();

const path = require("path");

const { getCurrentVersion } = require("./scripts/utils/get-version");
const queries = require("./scripts/utils/algolia");

const version = getCurrentVersion();
const DOCS_PATH = path.join(__dirname, "versions", `${version}`);

module.exports = {
  siteMetadata: {
    title: "Dagster",
    description: "Dagster official website",
    author: "@dagster"
  },
  plugins: [
    "gatsby-plugin-react-helmet",
    {
      resolve: `gatsby-plugin-algolia`,
      options: {
        queries: process.env.GATSBY_SHOULD_DEPLOY_TO_ALGOLIA ? queries : [],
        appId: process.env.GATSBY_ALGOLIA_APP_ID || process.env.ALGOLIA_APP_ID,
        apiKey: process.env.ALGOLIA_ADMIN_KEY,
        chunkSize: 10000 // default: 1000
      }
    },
    {
      resolve: "gatsby-source-filesystem",
      options: {
        name: "images",
        path: `${__dirname}/src/images`
      }
    },
    {
      resolve: "gatsby-source-filesystem",
      options: {
        name: "images",
        path: `${DOCS_PATH}/_images`
      }
    },
    "gatsby-plugin-theme-ui",
    "gatsby-transformer-sharp",
    "gatsby-plugin-sharp",
    {
      resolve: "gatsby-transformer-json",
      options: {
        typeName: "SphinxPage"
      }
    },
    {
      resolve: "gatsby-source-filesystem",
      options: {
        name: "docs",
        path: DOCS_PATH,
        ignore: [
          "**/globalcontext.json",
          "**/search.json",
          "**/searchindex.json"
        ]
      }
    },
    {
      resolve: "gatsby-plugin-resolve-src",
      options: {
        addSassLoader: false
      }
    },
    {
      resolve: `gatsby-plugin-alias-imports`,
      options: {
        alias: {
          "~dagster-info": path.join(__dirname, "dagster-info.json")
        }
      }
    },
    {
      resolve: "gatsby-plugin-typography",
      options: {
        pathToConfigModule: `${__dirname}/src/utils/typography`
      }
    },
    {
      resolve: "gatsby-plugin-exclude",
      options: {
        paths: ["/dagster/**"]
      }
    },
    {
      resolve: "gatsby-plugin-manifest",
      options: {
        name: "gatsby-starter-default",
        short_name: "starter",
        start_url: "/",
        background_color: "#663399",
        theme_color: "#663399",
        display: "minimal-ui",
        icon: "src/images/logo.png"
      }
    }
  ]
};
