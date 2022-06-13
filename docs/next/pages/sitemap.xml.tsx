import { latestAllVersionedPaths } from "util/useNavigation";

const toUrl = (host, route) => `<url><loc>http://${host}${route}</loc></url>`;

const createSitemap = (host, routes) =>
  `<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    ${routes.map((route) => toUrl(host, route)).join("")}
    </urlset>`;

const Sitemap = () => {};

Sitemap.getInitialProps = ({ res, req }) => {
  const routes = latestAllVersionedPaths().map(
    ({ params }) => "/" + params.page.join("/")
  );
  const sitemap = createSitemap(req.headers.host, routes);

  res.setHeader("Content-Type", "text/xml");
  res.write(sitemap);
  res.end();
  return res;
};

export default Sitemap;
