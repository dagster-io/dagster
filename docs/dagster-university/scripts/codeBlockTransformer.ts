import {promises as fs} from 'fs';
import path from 'path';

import {Node} from 'hast';
import visit from 'unist-util-visit';

import {limitSnippetLines} from './limit';

const DAGSTER_REPO = process.env.DAGSTER_REPO || path.join(__dirname, '../../../');

const DOCS_SNIPPET = path.join(DAGSTER_REPO, '/examples/docs_snippets/docs_snippets');

export interface CodeBlockStats {
  totalCodeBlocks: number;
  updatedCodeBlocks: string[];
}

interface CodeTransformerOptions {
  setCodeBlockStats?: (newStats: CodeBlockStats) => void;
}

const normalizeOptionValue = (value: string): string | boolean => {
  if (value === 'true') {
    return true;
  } else if (value === 'false') {
    return false;
  } else {
    return value;
  }
};

export default ({setCodeBlockStats: setCodeBlockStats}: CodeTransformerOptions) =>
  async (tree: Node) => {
    const codes: [Node, number][] = [];
    visit(tree, 'code', (node, index) => {
      codes.push([node, index]);
    });

    const optionKeys = ['lines', 'startafter', 'endbefore', 'dedent', 'trim'];

    const stats: CodeBlockStats = {
      totalCodeBlocks: 0,
      updatedCodeBlocks: [],
    };

    for (const [node] of codes) {
      const meta = ((node['meta'] as string) || '').split(' ');
      const fileMeta = meta.find((m) => m.startsWith('file='));
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

      const filePath = fileMeta.slice('file='.length);
      const fileAbsPath = path.join(DOCS_SNIPPET, filePath);
      try {
        const content = await fs.readFile(fileAbsPath, 'utf8');
        let contentWithLimit = limitSnippetLines(
          content,
          metaOptions.lines,
          metaOptions.dedent,
          metaOptions.startafter,
          metaOptions.endbefore,
        );

        // remove pragmas
        contentWithLimit = contentWithLimit.replace(/^\s*# (type|ruff|isort|noqa):.*$/g, '');
        contentWithLimit = contentWithLimit.replace(/  # (type|ruff|isort|noqa):.*$/g, '');

        if (metaOptions.trim) {
          contentWithLimit = contentWithLimit.trim();
        }

        stats.totalCodeBlocks++;
        if (node['value'] !== contentWithLimit) {
          stats.updatedCodeBlocks.push(node['meta'] as string);
          node['value'] = `${contentWithLimit}`;
        }
      } catch (err) {
        node['value'] = err.message;
      }
    }

    if (setCodeBlockStats) {
      setCodeBlockStats(stats);
    }
  };
