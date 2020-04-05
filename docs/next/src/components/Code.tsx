import SyntaxHighlighter from 'react-syntax-highlighter';
import { dracula } from 'react-syntax-highlighter/dist/cjs/styles/hljs';

const Code: React.FunctionComponent<{
  children: string;
  className: string;
  showLines?: boolean;
  startLine?: string;
}> = ({ children, className, showLines = false, startLine = '1' }) => {
  const language = className.replace(/language-/, '');

  return (
    <SyntaxHighlighter
      language={language}
      style={dracula}
      showLineNumbers={showLines}
      startingLineNumber={parseInt(startLine)}
    >
      {children}
    </SyntaxHighlighter>
  );
};

export default Code;
