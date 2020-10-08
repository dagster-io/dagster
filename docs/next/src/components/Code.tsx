import SyntaxHighlighter from 'react-syntax-highlighter';
import { tomorrowNight } from 'react-syntax-highlighter/dist/cjs/styles/hljs';
import Transition from 'components/Transition';
import CopyToClipboard from 'react-copy-to-clipboard';

import cx from 'classnames';
import { useState } from 'react';

const CopyButton: React.FC<{ code: string; inline?: boolean }> = ({
  code,
  inline = true,
}) => {
  const [tooltip, setTooltip] = useState(false);

  const onClick = () => {
    setTooltip(true);
    setTimeout(() => {
      setTooltip(false);
    }, 3000);
  };

  return (
    <div className="relative">
      <Transition
        show={tooltip}
        appear={true}
        enter="transition ease-out duration-100 transform"
        enterFrom="opacity-0 scale-95"
        enterTo="opacity-100 scale-100"
        leave="transition ease-in duration-300 transform"
        leaveFrom="opacity-100 scale-100"
        leaveTo="opacity-0 scale-95"
      >
        <div
          className={cx({
            'absolute right-6 -my-1': inline,
            'absolute right-0 top-8 z-10': !inline,
          })}
        >
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium leading-4 bg-gray-100 text-gray-800">
            Copied
          </span>
        </div>
      </Transition>

      <CopyToClipboard text={code}>
        <svg
          className="h-5 w-5 text-gray-400 cursor-pointer hover:text-gray-300 transition-colors duration-300"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          onClick={onClick}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          />
        </svg>
      </CopyToClipboard>
    </div>
  );
};

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
  // console.log(props);

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
        <div className="bg-gray-800 px-2 pb-3 pt-2 text-white rounded text-sm flex justify-between">
          <div>{caption}</div>
          <CopyButton code={code} />
        </div>
      )}
      <div className={cx('relative', { '-mt-2': caption })}>
        {!caption && (
          <div className="absolute right-0 mr-3 mt-2 h-3 w-3">
            <CopyButton code={code} inline={true} />
          </div>
        )}
        <SyntaxHighlighter
          language={language}
          style={tomorrowNight}
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
