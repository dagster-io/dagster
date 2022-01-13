import 'highlight.js/styles/xcode.css';

/* eslint-disable @typescript-eslint/ban-ts-comment */
// https://github.com/highlightjs/highlight.js/issues/2682

// @ts-ignore
import hljs from 'highlight.js/lib/core';
// @ts-ignore
import sql from 'highlight.js/lib/languages/sql';
// @ts-ignore
import yaml from 'highlight.js/lib/languages/yaml';
import * as React from 'react';

const {configure, highlightBlock} = hljs;

hljs.registerLanguage('sql', sql);
hljs.registerLanguage('yaml', yaml);

interface Props {
  value: string;
  language: 'yaml' | 'sql' | 'py';
  className?: string;
  style?: React.CSSProperties;
}

export const HighlightedCodeBlock = (props: Props) => {
  const {language, value, ...rest} = props;
  const node = React.useRef(null);

  React.useEffect(() => {
    if (node.current) {
      configure({languages: [language]});
      highlightBlock(node.current);
    }
  }, [language]);

  return (
    <pre
      ref={node}
      {...rest}
      style={{backgroundColor: 'transparent', margin: 0, padding: 0, ...(rest.style || {})}}
    >
      {value}
    </pre>
  );
};
