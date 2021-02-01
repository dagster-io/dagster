import visit from "unist-util-visit";
import { promises as fs } from "fs";
import path from "path";

import { limitSnippetLines } from "./limit";

const DAGSTER_REPO =
  process.env.DAGSTER_REPO || path.join(__dirname, "../../../");

const DOCS_SNIPPET = path.join(
  DAGSTER_REPO,
  "/examples/docs_snippets/docs_snippets"
);

export default () => async (tree) => {
  const codes = [];
  visit(tree, "code", (node, index, parent) => {
    codes.push([node, index, parent]);
  });

  const optionKeys = ["lines", "startafter", "endbefore", "dedent", "trim"];

  let totalSnapshots = 0;
  let updatedSnapshots = [];

  for (const [node] of codes) {
    const meta = (node.meta || "").split(" ");
    const fileMeta = meta.find((m) => m.startsWith("file="));
    if (!fileMeta) {
      continue;
    }

    const metaOptions: {
      lines?: string;
      dedent?: string;
      startafter?: string;
      endbefore?: string;
      trim?: boolean;
    } = {};
    for (const option of optionKeys) {
      const needle = `${option}=`;
      const value = meta.find((m) => m.startsWith(needle));
      if (value) {
        metaOptions[option] = value.slice(needle.length);
      }
    }

    const filePath = fileMeta.slice("file=".length);
    const fileAbsPath = path.join(DOCS_SNIPPET, filePath);
    try {
      const content = await fs.readFile(fileAbsPath, "utf8");
      let contentWithLimit = limitSnippetLines(
        content,
        metaOptions.lines,
        metaOptions.dedent,
        metaOptions.startafter,
        metaOptions.endbefore
      );

      if (metaOptions.trim) {
        contentWithLimit = contentWithLimit.trim();
      }

      totalSnapshots++;
      if (node.value !== contentWithLimit) {
        updatedSnapshots.push(node.meta);
        node.value = `${contentWithLimit}`;
      }
    } catch (err) {
      node.value = err.message;
    }
  }

  console.log(`✅ ${totalSnapshots} snapshots parsed`);
  if (updatedSnapshots.length) {
    console.log(`⚡️ ${updatedSnapshots.length} updated:`);
    console.log(`\t${updatedSnapshots.join("\n\t")}`);
  } else {
    console.log(`✨ No snapshots were updated`);
  }
};
