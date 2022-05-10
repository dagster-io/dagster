import fs, { link } from "fs";
import path from "path";
import fg from "fast-glob";
import { Node } from "hast";
import visit from "unist-util-visit";
import matter from "gray-matter";

// remark
import mdx from "remark-mdx";
import remark from "remark";

const ROOT_DIR = path.resolve(__dirname, "../../");
const DOCS_DIR = path.resolve(ROOT_DIR, "content");
const DAGSTER_DIR = path.resolve(ROOT_DIR, "..")
interface LinkElement extends Node {
  type: "link" | "image";
  url: string;
}


test("No dead external MDX links", async () => {
  const allMdxFilePaths = await fg(["**/*.mdx"], { cwd: DOCS_DIR });

  const astStore: { [filePath: string]: Node } = {};
  const allExternalLinksStore: { [filePath: string]: Array<string> } = {};

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
    const externalLinks = collectExternalLinks(astStore[filePath]);
    allExternalLinksStore[filePath] = externalLinks;
  }

  const deadLinks: Array<{ sourceFile: string; deadLink: string }> = [];

  let linkCount = 0;

  for (const source in allExternalLinksStore) {
    const linkList = allExternalLinksStore[source];

    for (const link of linkList) {
      linkCount++;
      if (!isLinkLegit(link)) {
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


function isLinkLegit(
  rawTarget: string,
): boolean {
  // TODO: Validate links to API Docs

  const splitter = new RegExp('\/master\/')

  const filePath = rawTarget.split(splitter)[1]

  return fileExists(path.resolve(DAGSTER_DIR, filePath))
}

// traverse the mdx ast to find all links to our examples
function collectExternalLinks(
  tree: Node,
): Array<string> {
  const externalLinkRegex = /^(https?:\/\/github\.com\/dagster\-io\/dagster\/.*\/master)/;
  const result: Array<string> = [];

  visit(tree, ["link", "image"], (node: LinkElement, index) => {
    const { url } = node;
    if (url.match(externalLinkRegex)) {
      result.push(url);
    } else {
      return;
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
