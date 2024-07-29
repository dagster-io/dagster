import {Transition} from '@headlessui/react';
import Prism from 'prismjs';
import React from 'react';
import 'prismjs/components/prism-python';
import {useCopyToClipboard} from 'react-use';

Prism.manual = true;

export const Fence = (props) => {
  const text = props.children;
  const language = props['data-language'];
  const [copied, setCopied] = React.useState(false);
  const [state, copy] = useCopyToClipboard();

  React.useEffect(() => {
    Prism.highlightAll();
  }, [text]);

  const copyToClipboard = React.useCallback(() => {
    if (typeof text === 'string') {
      copy(text);
      setCopied(true);
      setTimeout(() => {
        setCopied(false);
      }, 3000);
    }
  }, [copy, text]);

  return (
    <div className="codeBlock relative" aria-live="polite">
      <pre className="line-numbers">
        <code className={`language-${language}`}>{text}</code>
      </pre>
      <div className="absolute top-2 right-2">
        <Transition
          show={true}
          appear={true}
          enter="transition-opacity duration-150"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="transition-opacity duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          {copied ? (
            <span className="select-none inline-flex items-center px-2 rounded text-xs font-medium leading-4 bg-gray-900 text-gray-400">
              Copied
            </span>
          ) : (
            <svg
              className="h-5 w-5 text-gray-400 cursor-pointer hover:text-gray-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              onClick={copyToClipboard}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
          )}
        </Transition>
      </div>
    </div>
  );
};
