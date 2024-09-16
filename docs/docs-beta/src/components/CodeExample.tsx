import React from 'react';
import CodeBlock from '@theme/CodeBlock';

interface CodeExampleProps {
  filePath: string;
  language?: string;
  title?: string;
}

const CodeExample: React.FC<CodeExampleProps> = ({filePath, language, title}) => {
  const [content, setContent] = React.useState<string>('');
  const [error, setError] = React.useState<string | null>(null);

  language = language || 'python';

  React.useEffect(() => {
    // Adjust the import path to start from the docs directory
    import(`!!raw-loader!/../../examples/docs_beta_snippets/docs_beta_snippets/${filePath}`)
      .then((module) => {
        const lines = module.default.split('\n').map((line) => {
          return line.replaceAll(/#.*?noqa.*?$/g, '');
        });
        const mainIndex = lines.findIndex((line) => line.trim().startsWith('if __name__ == '));
        const strippedContent =
          mainIndex !== -1 ? lines.slice(0, mainIndex).join('\n') : lines.join('\n');
        setContent(strippedContent);
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
    <CodeBlock language={language} title={title}>
      {content || 'Loading...'}
    </CodeBlock>
  );
};

export default CodeExample;
