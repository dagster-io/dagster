import React from 'react';
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

const CodeExample: React.FC<CodeExampleProps> = ({
  filePath,
  language,
  title,
  lineStart,
  lineEnd,
  ...props
}) => {
  const [content, setContent] = React.useState<string>('');
  const [error, setError] = React.useState<string | null>(null);

  language = language || 'python';

  React.useEffect(() => {
    // Adjust the import path to start from the docs directory
    import(`!!raw-loader!/../../examples/docs_beta_snippets/docs_beta_snippets/${filePath}`)
      .then((module) => {
        var lines = module.default.split('\n');

        const sliceStart = lineStart && lineStart > 0 ? lineStart : 0;
        const sliceEnd = lineEnd && lineEnd <= lines.length ? lineEnd : lines.length;
        lines = lines.slice(sliceStart, sliceEnd);

        lines = filterNoqaComments(lines);
        lines = trimMainBlock(lines);

        setContent(lines.join('\n'));
        setError(null);
      })
      .catch((error) => {
        console.error(`Error loading file: ${filePath}`, error);
        setError(
          `Failed to load file: ${filePath}. Please check if the file exists and the path is correct.`,
        );
      });
  }, [filePath]);

  if (error) {
    return <div style={{color: 'red', padding: '1rem', border: '1px solid red'}}>{error}</div>;
  }

  return (
    <CodeBlock language={language} title={title} {...props}>
      {content || 'Loading...'}
    </CodeBlock>
  );
};

export default CodeExample;
