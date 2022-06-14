import { Node } from "hast";
import { promises as fs } from "fs";
import { limitSnippetLines } from "./limit";
import path from "path";
import visit from "unist-util-visit";

const DAGSTER_REPO =
  process.env.DAGSTER_REPO || path.join(__dirname, "../../../");

const DOCS_SNIPPET = path.join(
  DAGSTER_REPO,
  "/examples/docs_snippets/docs_snippets"
);

export interface SnapshotStats {
  totalSnapshots: number;
  updatedSnapshots: string[];
}

interface CodeTransformerOptions {
  setSnapshotStats?: (newStats: SnapshotStats) => void;
}

const normalizeOptionValue = (value: string): string | boolean => {
  if (value === 'true') { return true; }
  else if (value === 'false') { return false; }
  else { return value; }
}

export default ({ setSnapshotStats }: CodeTransformerOptions) => async (
  tree: Node
) => {
  const codes: [Node, number][] = [];
  visit(tree, "code", (node, index) => {
    codes.push([node, index]);
  });

  const optionKeys = ["lines", "startafter", "endbefore", "dedent", "trim"];

  const stats: SnapshotStats = {
    totalSnapshots: 0,
    updatedSnapshots: [],
  };

  for (const [node] of codes) {
    const meta = ((node["meta"] as string) || "").split(" ");
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
    } = {
      trim: true,
    };

    for (const option of optionKeys) {
      const needle = `${option}=`;
      const value = meta.find((m) => m.startsWith(needle));
      if (value) {
        metaOptions[option] = normalizeOptionValue(value.slice(needle.length));
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

      stats.totalSnapshots++;
      if (node["value"] !== contentWithLimit) {
        stats.updatedSnapshots.push(node["meta"] as string);
        node["value"] = `${contentWithLimit}`;
      }
    } catch (err) {
      node["value"] = err.message;
    }
  }

  if (setSnapshotStats) {
    setSnapshotStats(stats);
  }
};
