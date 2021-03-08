import fs from "fs";
import path from "path";
import fg from "fast-glob";
import { Node } from "hast";
import visit from "unist-util-visit";

// remark
import mdx from "remark-mdx";
import remark from "remark";
import { createCompiler } from "@mdx-js/mdx";

const ROOT_DIR = path.resolve(__dirname, "../");
const DOCS_DIR = path.resolve(ROOT_DIR, "content");

interface LinkElement extends Node {
  type: "link" | "image";
  url: string;
}

test("no dead links", async () => {
  const allMdxFilePaths = await fg(["**/*.mdx"], { cwd: DOCS_DIR });

  const astStore: { [filePath: string]: Node } = {};
  const allInternalLinksStore: { [filePath: string]: Array<string> } = {};

  // Parse mdx files to find all internal links and populate the store
  await Promise.all(
    allMdxFilePaths.map(async (relativeFilePath) => {
      const absolutePath = path.resolve(DOCS_DIR, relativeFilePath);
      const fileContent = await fs.promises.readFile(absolutePath, "utf-8");
      astStore[relativeFilePath] = remark().use(mdx).parse(fileContent);
    })
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
          sourceFile: path.resolve(DOCS_DIR, source),
          deadLink: link,
        });
      }
    }
  }

  // Sanity check to make sure the parser is working
  expect(linkCount).toBeGreaterThan(0);

  expect(deadLinks).toEqual([]);
});

function getMatchCandidates(targetPath: string): Array<string> {
  return [`${targetPath}.mdx`, `${targetPath}/index.mdx`];
}

function isLinkLegit(
  rawTarget: string,
  allMdxFileSet: Set<string>,
  astStore: { [filePath: string]: Node }
): boolean {
  // TODO: Validate links to API Docs
  if (rawTarget.startsWith("_apidocs/")) {
    return true;
  }

  // Validate links to public assets
  if (rawTarget.startsWith("assets/")) {
    return fileExists(path.resolve(ROOT_DIR, "public", rawTarget));
  }

  // Validate regular content links
  if (!rawTarget.includes("#")) {
    // the link target doesn't have a "#" anchor
    return getMatchCandidates(rawTarget).some((name) =>
      allMdxFileSet.has(name)
    );
  }

  // Todo: Validate links with anchors
  const [target, anchor] = rawTarget.split("#");
  const targetFilePath = getMatchCandidates(target).find((name) =>
    allMdxFileSet.has(name)
  );
  if (targetFilePath) {
    // const allAnchors = collectHeadingsAsAnchors(astStore[targetFilePath]);
    // return allAnchors.includes(anchor);
    return true;
  }

  return false;
}

// traverse the mdx ast to find all internal links
function collectInternalLinks(
  tree: Node,
  currentFilePath: string
): Array<string> {
  const externalLinkRegex = /^https?:\/\//;
  const result: Array<string> = [];

  visit(tree, ["link", "image"], (node: LinkElement, index) => {
    const { url } = node;
    if (url.match(externalLinkRegex)) {
      return;
    }

    if (url.startsWith("#")) {
      // is a self-referencing anchor link
      result.push(`${currentFilePath.replace(/\.mdx$/, "")}${url}`);
    } else if (!url.startsWith("/")) {
      // TODO links should all be absolute paths
      // throw new Error(
      //   `Do not use relative references ('${url}' in ${currentFilePath}). All links should start with '/'`,
      // );
    } else {
      // remove the leading `/` from the link target
      result.push(url.substr(1));
    }
  });

  return result;
}

function fileExists(filePath: string): boolean {
  try {
    fs.statSync(filePath);
    return true;
  } catch (_) {
    return false;
  }
}
