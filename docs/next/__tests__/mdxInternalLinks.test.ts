import fs, { link } from "fs";
import path from "path";
import fg from "fast-glob";
import { Node } from "hast";
import visit from "unist-util-visit";
import { flatten } from "../util/useNavigation";
import masterNavigation from "../../content/_navigation.json";
import generateToc from "mdast-util-toc";
import { getItems, getIds } from "../components/mdx/SidebarNavigation";
import matter from "gray-matter";

// remark
import mdx from "remark-mdx";
import remark from "remark";

const DAGSTER_DIR = path.resolve(__dirname, "../../..");
const ROOT_DIR = path.resolve(__dirname, "../../");
const DOCS_DIR = path.resolve(ROOT_DIR, "content");
interface LinkElement extends Node {
  type: "link" | "image";
  url: string;
}

test("No dead navs", async () => {
  const deadNavLinks: Array<{ title: string; deadLink: string }> = [];
  flatten(masterNavigation).forEach((elem) => {
    if (elem.path == null) {
      return;
    }
    if (elem.path.startsWith("/_apidocs")) {
      // TODO: Validate links to API Docs
      return;
    }
    if (
      elem.path &&
      !fileExists(path.join(DOCS_DIR, elem.path) + ".mdx") &&
      !elem.isExternalLink &&
      !elem.isUnversioned
    ) {
      deadNavLinks.push({
        title: elem.title,
        deadLink: elem.path,
      });
    }
  });

  expect(deadNavLinks).toEqual([]);
});

test("No dead MDX links", async () => {
  const allMdxFilePaths = await fg(["**/*.mdx"], { cwd: DOCS_DIR });

  const astStore: { [filePath: string]: Node } = {};
  const allInternalLinksStore: { [filePath: string]: Array<string> } = {};

  // Parse mdx files to find all internal links and populate the store
  await Promise.all(
    allMdxFilePaths.map(async (relativeFilePath) => {
      const absolutePath = path.resolve(DOCS_DIR, relativeFilePath);
      const fileContent = await fs.promises.readFile(absolutePath, "utf-8");
      // separate content and front matter data
      const { content, data } = matter(fileContent);
      astStore[relativeFilePath] = remark().use(mdx).parse(content);
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

test("No dead GraphQL schema", async () => {
  const graphqlSchemaExists = fileExists(path.resolve(DAGSTER_DIR, "js_modules/dagit/packages/core/src/graphql/schema.graphql"))

  expect(graphqlSchemaExists).toBe(true);
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
  if (rawTarget.startsWith("assets/") || rawTarget.startsWith("images/")) {
    return fileExists(path.resolve(ROOT_DIR, "next/public", rawTarget));
  }

  // Validate regular content links
  if (!rawTarget.includes("#")) {
    // the link target doesn't have a "#" anchor
    return getMatchCandidates(rawTarget).some((name) =>
      allMdxFileSet.has(name)
    );
  }

  // Validate links with anchors
  const [target, anchor] = rawTarget.split("#");
  const targetFilePath = getMatchCandidates(target).find((name) =>
    allMdxFileSet.has(name)
  );
  if (targetFilePath) {
    const allAnchors = collectHeadingsAsAnchors(astStore[targetFilePath]);
    return allAnchors.includes(anchor);
  }

  return false;
}

// traverse the mdx ast to find all internal links
function collectInternalLinks(
  tree: Node,
  currentFilePath: string
): Array<string> {
  const externalLinkRegex = /^(https?:\/\/|mailto:)/;
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
      throw new Error(
        `Do not use relative references ('${url}' in ${currentFilePath}). All links should start with '/'`
      );
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

function collectHeadingsAsAnchors(tree: Node): string[] {
  const node = generateToc(tree, {});
  const tableOfContents = getItems(node.map, {});
  return getIds(tableOfContents.items[0].items);
}
