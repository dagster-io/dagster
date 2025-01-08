import React, {Suspense} from 'react';
import CodeBlock from '@theme/CodeBlock';

interface CodeExampleProps {
  filePath: string;
  language?: string;
  title?: string;
  lineStart?: number;
  lineEnd?: number;
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
}: {
  cacheKey: string;
  module: any;
  lineStart?: number;
  lineEnd?: number;
}) {
  var lines = module.default.split('\n');

  const sliceStart = lineStart && lineStart > 0 ? lineStart : 0;
  const sliceEnd = lineEnd && lineEnd <= lines.length ? lineEnd : lines.length;
  lines = lines.slice(sliceStart, sliceEnd);

  lines = filterNoqaComments(lines);
  lines = trimMainBlock(lines);
  contentCache[cacheKey] = {content: lines.join('\n')};
}

function useLoadModule(cacheKey: string, path: string, lineStart: number, lineEnd: number) {
  const isServer = typeof window === 'undefined';
  if (isServer) {
    /**
     * Note: Remove the try/catch to cause a hard error on build once all of the bad code examples are cleaned up.
     */
    try {
      const module = require(`!!raw-loader!/../../examples/${path}`);
      processModule({cacheKey, module, lineStart, lineEnd});
    } catch (e) {
      console.error(e);
      contentCache[cacheKey] = {error: e.toString()};
    }
  }

  if (!contentCache[cacheKey]) {
    /**
     * We only reach this path on the client.
     * Throw a promise to suspend in order to avoid un-rendering the codeblock that we SSR'd
     */
    throw import(`!!raw-loader!/../../examples/${path}`)
      .then((module) => {
        processModule({cacheKey, module, lineStart, lineEnd});
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
  const {filePath, title, lineStart, lineEnd, language = 'python', ...extraProps} = props;

  const path = 'docs_beta_snippets/docs_beta_snippets/' + filePath;
  const cacheKey = JSON.stringify(props);
  const {content, error} = useLoadModule(cacheKey, path, lineStart, lineEnd);

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
