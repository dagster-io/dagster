import {Transition} from '@headlessui/react';
import Prism from 'prismjs';
import React from 'react';
import 'prismjs/components/prism-python';
import { useCopyToClipboard } from 'react-use';

Prism.manual = true;


export const Fence = (props) => {
  const text = props.children;
  const language = props['data-language'];
  const [copied, setCopied] = React.useState(false);
  const [state, copy] = useCopyToClipboard();

  React.useEffect(() => {
    Prism.highlightAll();
  }, []);


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
    <div aria-live="polite">
      <pre className="line-numbers" onClick={copyToClipboard}>
        <code className={`language-${language}`}> {text} </code>
      </pre>
    </div>
  );
};
