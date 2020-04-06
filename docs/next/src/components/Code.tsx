import SyntaxHighlighter from 'react-syntax-highlighter';
import { dracula } from 'react-syntax-highlighter/dist/cjs/styles/hljs';

type CodeProps = {
  children: string;
  className: string;
  showLines?: boolean;
  startLine?: string;
  'emphasize-lines'?: string;
};

const Code: React.FunctionComponent<CodeProps> = ({
  children,
  className,
  showLines = false,
  startLine = '1',
  ...props
}) => {
  const language = className.replace(/language-/, '');

  const emphasizeLines = props['emphasize-lines'];
  const rangesToEmphasize = emphasizeLines
    ? emphasizeLines
        .split(',')
        .map((s) => s.trim())
        .map((s) => s.split('-').map((e) => parseInt(e)))
    : [];
    
  return (
    <SyntaxHighlighter
      language={language}
      style={dracula}
      showLineNumbers={showLines}
      startingLineNumber={parseInt(startLine)}
      wrapLines={true}
      lineProps={(lineNumber: number) => {
        const ln = lineNumber;
        let shouldHighlightLine = false;
        for (const [start, end] of rangesToEmphasize) {
          if (!end) if (ln === start) shouldHighlightLine = true;
          if (ln >= start && ln <= end) shouldHighlightLine = true;
        }
        return {
          style: {
            display: 'block',
            backgroundColor: shouldHighlightLine ? '#001F86' : undefined,
          },
        };
      }}
    >
      {children}
    </SyntaxHighlighter>
  );
};

export default Code;
