import * as React from 'react';
import 'highlight.js/styles/github.css';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import rehypeSanitize, {defaultSchema} from 'rehype-sanitize';
import gfm from 'remark-gfm';

const sanitizeConfig = {
  ...defaultSchema,
  protocols: {
    src: [...(defaultSchema.protocols?.src ?? []), 'data'],
  },
  attributes: {
    ...defaultSchema.attributes,
    span: [
      ...(defaultSchema.attributes?.span || []),
      // List of all allowed tokens:
      [
        'className',
        'hljs-addition',
        'hljs-attr',
        'hljs-attribute',
        'hljs-built_in',
        'hljs-bullet',
        'hljs-char',
        'hljs-code',
        'hljs-comment',
        'hljs-deletion',
        'hljs-doctag',
        'hljs-emphasis',
        'hljs-formula',
        'hljs-keyword',
        'hljs-link',
        'hljs-literal',
        'hljs-meta',
        'hljs-name',
        'hljs-number',
        'hljs-operator',
        'hljs-params',
        'hljs-property',
        'hljs-punctuation',
        'hljs-quote',
        'hljs-regexp',
        'hljs-section',
        'hljs-selector-attr',
        'hljs-selector-class',
        'hljs-selector-id',
        'hljs-selector-pseudo',
        'hljs-selector-tag',
        'hljs-string',
        'hljs-strong',
        'hljs-subst',
        'hljs-symbol',
        'hljs-tag',
        'hljs-template-tag',
        'hljs-template-variable',
        'hljs-title',
        'hljs-type',
        'hljs-variable',
      ],
    ],
  },
};

interface Props {
  children: string;
}

export const MarkdownWithPlugins = (props: Props) => {
  return (
    <ReactMarkdown
      {...props}
      remarkPlugins={[gfm]}
      rehypePlugins={[rehypeHighlight, [rehypeSanitize, sanitizeConfig]]}
    />
  );
};

// eslint-disable-next-line import/no-default-export
export default MarkdownWithPlugins;
