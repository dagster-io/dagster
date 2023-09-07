import Prism from 'prismjs';

import * as React from 'react';

export function CodeBlock({children, 'data-language': language}) {
  const ref = React.useCallback((node: HTMLPreElement) => {
    if (node) {
      Prism.highlightElement(node, false);
    }
  }, []);

  return (
    <div className="code" aria-live="polite" style={{display: 'flex'}}>
      <pre
        ref={ref}
        className={`language-${language}`}
        style={{height: '100%', marginBottom: 0, marginTop: 0}}
      >
        {children}
      </pre>
      <style jsx>
        {`
          .code {
            position: relative;
          }

          /* Override Prism styles */
          .code :global(pre[class*='language-']) {
            text-shadow: none;
            border-radius: 4px;
          }
        `}
      </style>
    </div>
  );
}
