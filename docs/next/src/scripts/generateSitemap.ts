import fs from 'fs';
import globby from 'globby';
import { getApiDocsPaths } from '../lib/apiDocsPaths';
import parser from 'fast-xml-parser';

(async () => {
  // Ignore Next.js specific files (e.g., _app.js) and API routes.
  const pages = await globby([
    'src/pages/**/*.mdx',
    '!src/pages/apidocs/[...page]', // <- Exclude dynamic route
    '!src/pages/_modules/[...page]', // <- Exclude dynamic route
  ]);

  // API Docs
  const { paths } = getApiDocsPaths();
  const apiDocsPages = paths
    .map(({ params }) => params.page)
    .map((parts) => {
      return `/apidocs/${parts.join('/')}`;
    });

  // Combine them into the pages you care about
  let allPages = [...pages, ...apiDocsPages];

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    ${allPages
      .sort()
      .map((page) => {
        const path = page.replace('src/pages', '').replace('.mdx', '');
        const route = path === '/index' ? '' : path.replace(/\/index$/, '');

        return `
  <url>
        <loc>${`https://docs.dagster.io${route}`}</loc>
  </url>
`;
      })
      .join('')}
</urlset>
      `;

  // Validate XML (throws if not valid)
  parser.parse(sitemap, {}, true);

  fs.writeFileSync('public/sitemap.xml', sitemap);
})();
