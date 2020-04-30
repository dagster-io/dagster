import SyntaxHighlighter from 'react-syntax-highlighter';
import { dracula } from 'react-syntax-highlighter/dist/cjs/styles/hljs';
import cx from 'classnames';

type CodeProps = {
  children: string;
  className: string;
  showLines?: boolean;
  startLine?: string;
  'emphasize-lines'?: string;
  caption?: string;
};

const Code: React.FunctionComponent<CodeProps> = ({
  children,
  className,
  showLines = false,
  startLine = '1',
  ...props
}) => {
  const language = className ? className.replace(/language-/, '') : 'text';
  const emphasizeLines = props['emphasize-lines'];
  const caption = props['caption'];
  const rangesToEmphasize = emphasizeLines
    ? emphasizeLines
        .split(',')
        .map((s) => s.trim())
        .map((s) => s.split('-').map((e) => parseInt(e)))
    : [];

  // Remove the trailing new line from all code blocks.
  // This is needed to prevent extra spacing at the bottom of
  // the syntax highligher component.
  const code = children.replace(/\n+$/, '');

  return (
    <>
      {caption && (
        <div className="inline-block bg-gray-800 px-2 pb-2 pt-1 text-white rounded text-sm">
          {caption}
        </div>
      )}
      <div className={cx({ '-mt-2': caption })}>
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
              className: shouldHighlightLine ? 'highlighted-line' : '',
            };
          }}
        >
          {code}
        </SyntaxHighlighter>
      </div>
    </>
  );
};

export default Code;
