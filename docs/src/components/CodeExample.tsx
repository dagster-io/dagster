import React, {Suspense} from 'react';
import CodeBlock from '@theme/CodeBlock';

import {CODE_EXAMPLE_PATH_MAPPINGS} from '../code-examples-content';
import {dedentLines, trimMainBlock, filterComments} from '../utils/codeExampleUtils';

interface CodeExampleProps {
  path: string;
  language?: string;
  title?: string;
  lineStart?: number;
  lineEnd?: number;
  startAfter?: string; // marker that indicates beginning of code snippet
  endBefore?: string; // marker that indicates ending of code snippet
  dedent?: number;
}

const contentCache: Record<string, {content?: string; error?: string | null}> = {};

function processModule({
  cacheKey,
  module,
  lineStart,
  lineEnd,
  startAfter,
  endBefore,
  dedent,
}: {
  cacheKey: string;
  module: any;
  lineStart?: number;
  lineEnd?: number;
  startAfter?: string;
  endBefore?: string;
  dedent?: number;
}) {
  var lines = module.default.split('\n');

  // limit to range of `lineStart` and `lineEnd`
  const lineStartIndex = lineStart && lineStart > 0 ? lineStart : 0;
  const lineEndIndex = lineEnd && lineEnd <= lines.length ? lineEnd : lines.length;

  // limit to range of `startAfter` and `endBefore`
  let startAfterIndex = startAfter ? lines.findIndex((line: string) => line.includes(startAfter)) + 1 : 0;

  const endAfterIndex = endBefore ? lines.findIndex((line: string) => line.includes(endBefore)) : lines.length;

  const ix1 = Math.max(lineStartIndex, startAfterIndex);
  const ix2 = Math.min(lineEndIndex, endAfterIndex);

  lines = lines.slice(ix1, ix2);

  lines = filterComments(lines);

  lines = trimMainBlock(lines);

  if (dedent && dedent > 0) {
    lines = dedentLines(lines, dedent);
  }

  contentCache[cacheKey] = {content: lines.join('\n')};
}

export function useLoadModule(
  cacheKey: string,
  path: string,
  lineStart: number,
  lineEnd: number,
  startAfter: string,
  endBefore: string,
  dedent: number,
) {
  //const isServer = typeof window === 'undefined';
  //if (isServer) {
  //  const module = CODE_EXAMPLE_PATH_MAPPINGS[path];
  //  processModule({cacheKey, module, lineStart, lineEnd, startAfter, endBefore});
  //}

  if (!contentCache[cacheKey]) {
    /**
     * We only reach this path on the client.
     * Throw a promise to suspend in order to avoid un-rendering the codeblock that we SSR'd
     */
    throw CODE_EXAMPLE_PATH_MAPPINGS[path]()
      .then((module) => {
        processModule({
          cacheKey,
          module,
          lineStart,
          lineEnd,
          startAfter,
          endBefore,
          dedent,
        });
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
    path,
    title,
    lineStart,
    lineEnd,
    startAfter,
    endBefore,
    language = 'python',
    dedent = 0,
    ...extraProps
  } = props;

  const cacheKey = JSON.stringify(props);
  const {content, error} = useLoadModule(cacheKey, path, lineStart, lineEnd, startAfter, endBefore, dedent);

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
