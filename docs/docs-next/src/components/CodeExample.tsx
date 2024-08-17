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

  React.useEffect(() => {
    // Adjust the import path to start from the docs directory
    import(`!!raw-loader!/docs/code_examples/${filePath}`)
      .then((module) => {
        const lines = module.default.split('\n');
        const mainIndex = lines.findIndex((line) => line.trim().startsWith('if __name__ == '));
        const strippedContent =
          mainIndex !== -1 ? lines.slice(0, mainIndex).join('\n') : module.default;
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
    <CodeBlock language={language} title={title || filePath}>
      {content || 'Loading...'}
    </CodeBlock>
  );
};

export default CodeExample;
