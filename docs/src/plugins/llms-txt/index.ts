/**
 * Plugin to generate /llms.txt and /llms-full.txt
 *
 * Heavily inspired by the Prisma documentation (thank you!):
 *
 * - https://github.com/prisma/docs/blob/22208d52e4168028dbbe8b020b10682e6b526e50/docusaurus.config.ts
 *
 */

import path from 'node:path';
import fs from 'node:fs';

const EXCLUDED_DIRECTORIES = ['docs/partials'];

module.exports = function (context, options) {
  return {
    name: 'llms-txt-plugin',
    loadContent: async () => {
      const {siteDir} = context;
      const contentDir = path.join(siteDir, 'docs');
      const allMdx: string[] = [];

      // recursive function to get all mdx files
      const getMdxFiles = async (dir: string) => {
        const entries = await fs.promises.readdir(dir, {withFileTypes: true});

        for (const entry of entries) {
          if (EXCLUDED_DIRECTORIES.some((dir) => entry.path.endsWith(dir))) {
            continue;
          }

          const fullPath = path.join(dir, entry.name);
          if (entry.isDirectory()) {
            await getMdxFiles(fullPath);
          } else if (entry.name.endsWith('.mdx')) {
            const content = await fs.promises.readFile(fullPath, 'utf8');
            allMdx.push(content);
          }
        }
      };

      await getMdxFiles(contentDir);
      return {allMdx};
    },
    postBuild: async ({content, routes, outDir}) => {
      const {allMdx} = content as {allMdx: string[]};

      const concatenatedPath = path.join(outDir, 'llms-full.txt');
      await fs.promises.writeFile(concatenatedPath, allMdx.join('\n\n---\n\n'));

      const docsPluginRouteConfig = routes.filter((route) => route.plugin.name === 'docusaurus-plugin-content-docs')[0];

      const allDocsRouteConfig = docsPluginRouteConfig.routes?.filter((route) => route.path === '/')[0];

      if (!allDocsRouteConfig?.props?.version) {
        return;
      }

      // this route config has a `props` property that contains the current documentation.
      const currentVersionDocsRoutes = (allDocsRouteConfig.props.version as Record<string, unknown>).docs as Record<
        string,
        Record<string, unknown>
      >;

      // for every single docs route we now parse a path (which is the key) and a title
      const docsRecords = Object.entries(currentVersionDocsRoutes).map(([path, record]) => {
        return `- [${record.title}](${path}): ${record.description}`;
      });

      // Build up llms.txt file
      const llmsTxt = `# ${context.siteConfig.title}\n\n## Docs\n\n${docsRecords.join('\n')}`;

      // Write llms.txt file
      const llmsTxtPath = path.join(outDir, 'llms.txt');
      try {
        fs.writeFileSync(llmsTxtPath, llmsTxt);
      } catch (err) {
        throw err;
      }
    },
  };
};
