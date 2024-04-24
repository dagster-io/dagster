import Prism from 'prismjs';
import {Transition} from '@headlessui/react';
import * as React from 'react';

Prism.manual = true;

interface Props {
  children: React.ReactNode;
  'data-language': string;
  obfuscated: boolean;
}

const COPY_CONFIRMATION_MSC = 3000;

export const CodeBlock = (props: Props) => {
  const text = props.children;
  const language = props['data-language'];
  const {obfuscated} = props;

  const [hidden, setHidden] = React.useState(obfuscated);
  const [copied, setCopied] = React.useState(false);

  const copy = useCopyToClipboard();

  const copyToClipboard = React.useCallback(() => {
    if (typeof text === 'string') {
      copy(text);
      setCopied(true);
      setTimeout(() => {
        setCopied(false);
      }, COPY_CONFIRMATION_MSC);
    }
  }, [copy, text]);

  React.useEffect(() => {
    Prism.highlightAll();
  }, []);

  return (
    <div className="codeBlock relative" aria-live="polite" style={{display: 'flex'}}>
      <pre>
        <code className={`language-${language}`}>{text}</code>
      </pre>
      <Transition
        show={!copied}
        appear={true}
        enter="transition ease-out duration-150 transform"
        enterFrom="opacity-0 scale-95"
        enterTo="opacity-100 scale-100"
        leave="transition ease-in duration-150 transform"
        leaveFrom="opacity-100 scale-100"
        leaveTo="opacity-0 scale-95"
      >
        <div className="absolute top-2 right-1 mt-2 mr-2">
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
        </div>
      </Transition>
      <Transition
        show={copied}
        appear={true}
        enter="transition ease-out duration-150 transform"
        enterFrom="opacity-0 scale-95"
        enterTo="opacity-500 scale-100"
        leave="transition ease-in duration-200 transform"
        leaveFrom="opacity-100 scale-100"
        leaveTo="opacity-0 scale-95"
      >
        <div className="absolute top-2 right-1 mt-1 mr-2">
          <span className="select-none inline-flex items-center px-2 rounded text-xs font-medium leading-4 bg-gray-900 text-gray-400">
            Copied
          </span>
        </div>
      </Transition>
      {hidden ? (
        <div className="absolute backdrop-blur top-2 left-0 right-0 bottom-2 flex flex-row justify-center">
          <div className="mt-8">
            <button
              className="bg-white py-2 px-4 rounded-full transition hover:no-underline cursor-pointer border text-gable-green hover:text-gable-green-darker hover:border-gable-green"
              onClick={() => setHidden(false)}
            >
              View answer
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export const useCopyToClipboard = () => {
  const node = React.useRef<HTMLTextAreaElement | null>(null);

  React.useEffect(() => {
    node.current = document.createElement('textarea');
    node.current.style.position = 'fixed';
    node.current.style.top = '-10000px';
    document.body.appendChild(node.current);
    return () => {
      node.current && document.body.removeChild(node.current);
    };
  }, []);

  return React.useCallback((text: string) => {
    if (node.current) {
      node.current.value = text;
      node.current.select();
      document.execCommand('copy');
    }
  }, []);
};
