import Prism from 'prismjs';
import React from 'react';
import 'prismjs/components/prism-python';

Prism.manual = true;

// Define possible options for code blocks

export const Fence = ({children, 'data-language': language}) => {
  console.log(children, '\n', language);
  React.useEffect(() => {
    console.log('highlighting');
    Prism.highlightAll();
  }, []);

  return (
    <div aria-live="polite">
      <pre className="line-numbers">
        <code className={`language-${language}`}>
          {children}
        </code>
      </pre>
    </div>
  );
};
