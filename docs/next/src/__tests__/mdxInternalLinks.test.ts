import fs from 'fs';
import path from 'path';

import glob from 'glob';
import { createCompiler } from '@mdx-js/mdx';
import { getAnchorLinkFromHeadingContent } from 'components/AnchorHeading';

const { parse: parseMdxContent } = createCompiler();

const DOCS_ROOT = path.resolve(__dirname, '..', 'pages');

type MdxAstNode = any;

test('no dead links', async () => {
  const allMdxFilePaths = (await findAllMdxFileRelativePaths()).filter(
    (i) => !i.endsWith('versions/index.mdx'),
  );

  const astStore: { [filePath: string]: MdxAstNode } = {};
  const allInternalLinksStore: { [filePath: string]: Array<string> } = {};

  // parse mdx files to find all internal links and populate the store
  await Promise.all(
    allMdxFilePaths.map(async (relativeFilePath) => {
      const absolutePath = path.resolve(DOCS_ROOT, relativeFilePath);
      const fileContent = await fs.promises.readFile(absolutePath, 'utf-8');
      astStore[relativeFilePath] = parseMdxContent(fileContent);
    }),
  );

  for (const filePath in astStore) {
    const internalLinks = collectInternalLinks(astStore[filePath], filePath);
    allInternalLinksStore[filePath] = internalLinks;
  }

  const allMdxFileSet = new Set(allMdxFilePaths);
  const deadLinks: Array<{ sourceFile: string; deadLink: string }> = [];

  let linkCount = 0;

  for (const source in allInternalLinksStore) {
    const linkList = allInternalLinksStore[source];

    for (const link of linkList) {
      linkCount++;
      if (!isLinkLegit(link, allMdxFileSet, astStore)) {
        deadLinks.push({
          sourceFile: path.resolve(DOCS_ROOT, source),
          deadLink: link,
        });
      }
    }
  }

  // sanity check to make sure the parser is working
  expect(linkCount).toBeGreaterThan(0);

  expect(deadLinks).toEqual([]);
});

function getMatchCandidates(targetPath: string): Array<string> {
  return [`${targetPath}.mdx`, `${targetPath}/index.mdx`];
}

function isLinkLegit(
  rawTarget: string,
  allMdxFileSet: Set<string>,
  astStore: { [filePath: string]: MdxAstNode },
): boolean {
  if (rawTarget.startsWith('_apidocs/')) {
    // TODO: handle dynamic routes (which can also have "#" headings)
    return true;
  }

  if (!rawTarget.includes('#')) {
    // the link target doesn't have a "#" anchor
    return getMatchCandidates(rawTarget).some((name) =>
      allMdxFileSet.has(name),
    );
  }

  const [target, anchor] = rawTarget.split('#');

  const targetFilePath = getMatchCandidates(target).find((name) =>
    allMdxFileSet.has(name),
  );

  if (targetFilePath) {
    const allAnchors = collectHeadingsAsAnchors(astStore[targetFilePath]);
    return allAnchors.includes(`#${anchor}`);
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
function collectInternalLinks(
  rootAstNode: MdxAstNode,
  currentFilePath: string,
): Array<string> {
  const externalLinkRegex = /^https?:\/\//;

  const queue = [rootAstNode];
  const result: Array<string> = [];

  while (queue.length > 0) {
    const node = queue.shift();
    if (!node) {
      continue;
    }
    if (Array.isArray(node.children)) {
      queue.push(...node.children);
    }

    if (!(node.type === 'link' && node.url)) {
      continue;
    }

    const { url } = node;
    if (url.match(externalLinkRegex)) {
      continue;
    }

    if (url.startsWith('#')) {
      // is a self-referencing anchor link
      result.push(`${currentFilePath.replace(/\.mdx$/, '')}${url}`);
    } else if (!url.startsWith('/')) {
      throw new Error(
        `Do not use relative references ('${url}'). All links should start with '/'`,
      );
    } else if (url.startsWith('/assets/')) {
      // TODO: handle assets
    } else {
      // remove the leading `/` from the link target
      result.push(url.substr(1));
    }
  }

  return result;
}

function collectHeadingsAsAnchors(rootAstNode: MdxAstNode): Array<string> {
  const queue = [rootAstNode];
  const result: Array<string> = [];

  while (queue.length > 0) {
    const node = queue.shift();
    if (!node) {
      continue;
    }
    if (Array.isArray(node.children)) {
      queue.push(...node.children);
    }

    // NOTE: this matches the current behavior of <AnchorHeading />
    // where the children get flattened and only plain text is recognized
    if (
      node.type === 'heading' &&
      node.children.length === 1 &&
      node.children[0].type === 'text'
    ) {
      result.push(getAnchorLinkFromHeadingContent(node.children[0].value));
    }
  }

  return result;
}
