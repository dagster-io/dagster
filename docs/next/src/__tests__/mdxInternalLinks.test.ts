import fs from 'fs';
import path from 'path';

import glob from 'glob';
import { createCompiler } from '@mdx-js/mdx';

const { parse: parseMdxContent } = createCompiler();

const DOCS_ROOT = path.resolve(__dirname, '..', 'pages');

test('no dead links', async () => {
  const allMdxFilePaths = (await findAllMdxFileRelativePaths()).filter(
    (i) => !i.endsWith('versions/index.mdx'),
  );

  const allInternalLinksStore: { [filePath: string]: Array<string> } = {};

  // parse mdx files to find all internal links and populate the store
  await Promise.all(
    allMdxFilePaths.map(async (relativeFilePath) => {
      const absolutePath = path.resolve(DOCS_ROOT, relativeFilePath);
      const fileContent = await fs.promises.readFile(absolutePath, 'utf-8');

      const rootAstNode = parseMdxContent(fileContent);
      const internalLinks = collectInternalLinks(rootAstNode);

      allInternalLinksStore[relativeFilePath] = internalLinks;
    }),
  );

  const allMdxFileSet = new Set(allMdxFilePaths);
  const deadLinks: Array<{ sourceFile: string; deadLink: string }> = [];

  let linkCount = 0;

  for (const source in allInternalLinksStore) {
    const linkList = allInternalLinksStore[source];

    for (const link of linkList) {
      linkCount++;
      if (!isLinkLegit(link, allMdxFileSet)) {
        deadLinks.push({
          sourceFile: source,
          deadLink: link,
        });
      }
    }
  }

  // sanity check to make sure the parser is working
  expect(linkCount).toBeGreaterThan(0);

  expect(deadLinks).toEqual([]);
});

function isLinkLegit(rawTarget: string, allMdxFileSet: Set<string>): boolean {
  if (rawTarget.startsWith('_apidocs/')) {
    // TODO: handle dynamic routes (which can also have "#" headings)
    return true;
  }

  if (!rawTarget.includes('#')) {
    // the link target doesn't have a specific "#" heading/slug
    const candidates = [`${rawTarget}.mdx`, `${rawTarget}/index.mdx`];
    return candidates.some((name) => allMdxFileSet.has(name));
  }

  const [target, headingName] = rawTarget.split(/#+/);
  const headingLevel = (rawTarget.match(/#/g) || []).length;

  const targetFilePath = [`${target}.mdx`, `${target}/index.mdx`].find((name) =>
    allMdxFileSet.has(name),
  );

  if (targetFilePath) {
    // TODO: can read the mdx ast again and check if the heading/slug actually exists
    // (using the `headingName` and `headingLevel` above)
    return true;
  }

  return false;
}

// recursively find all filepaths relative to `DOCS_ROOT`
function findAllMdxFileRelativePaths(): Promise<Array<string>> {
  const options = {
    cwd: DOCS_ROOT,
  };

  return new Promise((resolve, reject) => {
    // NOTE: assuming all sources are `.mdx` files
    glob('**/*.mdx', options, (error, files) => {
      if (error) {
        reject(error);
        return;
      }
      resolve(files);
    });
  });
}

// traverse the mdx ast to find all internal links
function collectInternalLinks(rootAstNode: any): Array<string> {
  const externalLinkRegex = /^http/;

  const queue = [rootAstNode];
  const result = [];

  while (queue.length > 0) {
    const node = queue.shift();

    if (!node) {
      continue;
    }

    if (node.type === 'link' && node.url) {
      const { url } = node;
      if (!url.match(externalLinkRegex)) {
        if (url.startsWith('#')) {
          // TODO: handle self # heading links
        } else if (url.startsWith('/assets/')) {
          // TODO: handle assets
        } else if (url.startsWith('/')) {
          result.push(url.substr(1));
        } else {
          // disallow relative references
          result.push(
            `Do not use relative references ('${url}'). All links should start with '/'`,
          );
        }
      }
    }

    if (Array.isArray(node.children)) {
      queue.push(...node.children);
    }
  }

  return result;
}
