/**
 * Docusaurus always keeps the trailing slash on `baseUrl`, so the docs homepage advertises
 * `https://dagster.io/docs/` as its canonical, hreflang, and og:url. Vercel (`trailingSlash: false`)
 * redirects that URL to `https://dagster.io/docs`, so the homepage never references itself, which
 * SEO crawlers flag as a missing self-referencing hreflang. Rewrite the root URL after the build.
 *
 * The sitemap entry is fixed separately in the sitemap plugin's `createSitemapItems`, since
 * `postBuild` hooks run concurrently and the sitemap is written in its own `postBuild`.
 */
const fs = require('node:fs');
const path = require('node:path');

module.exports = function (context) {
  const rootUrl = `${context.siteConfig.url}${context.baseUrl}`;
  const fixedRootUrl = rootUrl.replace(/\/$/, '');

  return {
    name: 'root-url-without-trailing-slash',
    async postBuild({outDir}) {
      const indexPath = path.join(outDir, 'index.html');
      const html = await fs.promises.readFile(indexPath, 'utf8');
      await fs.promises.writeFile(indexPath, html.replaceAll(`"${rootUrl}"`, `"${fixedRootUrl}"`));
    },
  };
};
