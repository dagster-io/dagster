import React, {Suspense} from 'react';
import CodeBlock from '@theme/CodeBlock';

interface CodeExampleProps {
  filePath: string;
  language?: string;
  title?: string;
  lineStart?: number;
  lineEnd?: number;
  startAfter?: string; // marker that indicates beginning of code snippet
  endBefore?: string; // marker that indicates ending of code snippet
}

/**
 * Removes content below the `if __name__` block for the given `lines`.
 */
function trimMainBlock(lines: string[]): string[] {
  const mainIndex = lines.findIndex((line) => line.trim().startsWith('if __name__ == '));
  return mainIndex !== -1 ? lines.slice(0, mainIndex) : lines;
}

/**
 * Filters `noqa` comments from lines.
 */
function filterNoqaComments(lines: string[]): string[] {
  return lines.map((line: string) => {
    return line.replaceAll(/#.*?noqa.*?$/g, '');
  });
}

const contentCache: Record<string, {content?: string; error?: string | null}> = {};

function processModule({
  cacheKey,
  module,
  lineStart,
  lineEnd,
  startAfter,
  endBefore,
}: {
  cacheKey: string;
  module: any;
  lineStart?: number;
  lineEnd?: number;
  startAfter?: string;
  endBefore?: string;
}) {
  var lines = module.default.split('\n');

  // limit to range of `lineStart` and `lineEnd`
  const lineStartIndex = lineStart && lineStart > 0 ? lineStart : 0;
  const lineEndIndex = lineEnd && lineEnd <= lines.length ? lineEnd : lines.length;

  // limit to range of `startAfter` and `endBefore`
  let startAfterIndex = startAfter
    ? lines.findIndex((line: string) => line.includes(startAfter)) + 1
    : 0;

  const endAfterIndex = endBefore
    ? lines.findIndex((line: string) => line.includes(endBefore))
    : lines.length;

  const ix1 = Math.max(lineStartIndex, startAfterIndex);
  const ix2 = Math.min(lineEndIndex, endAfterIndex);

  lines = lines.slice(ix1, ix2);

  lines = filterNoqaComments(lines);
  lines = trimMainBlock(lines);
  contentCache[cacheKey] = {content: lines.join('\n')};
}

function useLoadModule(
  cacheKey: string,
  path: string,
  lineStart: number,
  lineEnd: number,
  startAfter: string,
  endBefore: string,
) {
  const isServer = typeof window === 'undefined';
  if (isServer) {
    const module = require(`!!raw-loader!/../../examples/${path}`);
    processModule({cacheKey, module, lineStart, lineEnd, startAfter, endBefore});
  }

  if (!contentCache[cacheKey]) {
    /**
     * We only reach this path on the client.
     * Throw a promise to suspend in order to avoid un-rendering the codeblock that we SSR'd
     */
    throw import(`!!raw-loader!/../../examples/${path}`)
      .then((module) => {
        processModule({cacheKey, module, lineStart, lineEnd, startAfter, endBefore});
      })
      .catch((e) => {
        contentCache[cacheKey] = {error: e.toString()};
      });
  }

  return contentCache[cacheKey];
}

const CodeExample: React.FC<CodeExampleProps> = ({...props}) => {
  return (
    <Suspense>
      <CodeExampleInner {...props} />
    </Suspense>
  );
};

const CodeExampleInner: React.FC<CodeExampleProps> = (props) => {
  const {
    filePath,
    title,
    lineStart,
    lineEnd,
    startAfter,
    endBefore,
    language = 'python',
    ...extraProps
  } = props;

  const path = 'docs_beta_snippets/docs_beta_snippets/' + filePath;
  const cacheKey = JSON.stringify(props);
  const {content, error} = useLoadModule(cacheKey, path, lineStart, lineEnd, startAfter, endBefore);

  if (error) {
    return <div style={{color: 'red', padding: '1rem', border: '1px solid red'}}>{error}</div>;
  }

  return (
    <CodeBlock language={language} title={title} {...extraProps}>
      {content || 'Loading...'}
    </CodeBlock>
  );
};

export default CodeExample;
