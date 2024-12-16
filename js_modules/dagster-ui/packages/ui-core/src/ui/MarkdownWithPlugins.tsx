import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import rehypeSanitize, {defaultSchema} from 'rehype-sanitize';
import gfm from 'remark-gfm';

import 'highlight.js/styles/github.css';
import { createGlobalStyle } from 'styled-components';
import { browserColorScheme, colorAccentBlue } from '@dagster-io/ui-components/src/theme/color';
import { Colors } from '@dagster-io/ui-components';

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

const GlobalStyle = createGlobalStyle`
  .hljs {
    color: #24292e;
    background: #fff
}

.hljs-doctag,.hljs-keyword,.hljs-meta .hljs-keyword,.hljs-template-tag,.hljs-template-variable,.hljs-type,.hljs-variable.language_ {
    color: ${Colors.textRed()}
}

.hljs-title,.hljs-title.class_,.hljs-title.class_.inherited__,.hljs-title.function_ {
    color: #6f42c1
}

.hljs-attr,.hljs-attribute,.hljs-literal,.hljs-meta,.hljs-number,.hljs-operator,.hljs-selector-attr,.hljs-selector-class,.hljs-selector-id,.hljs-variable {
    color: #005cc5
}

.hljs-meta .hljs-string,.hljs-regexp,.hljs-string {
    color: #032f62
}

.hljs-built_in,.hljs-symbol {
    color: #e36209
}

.hljs-code,.hljs-comment,.hljs-formula {
    color: #6a737d
}

.hljs-name,.hljs-quote,.hljs-selector-pseudo,.hljs-selector-tag {
    color: #22863a
}

.hljs-subst {
    color: #24292e
}

.hljs-section {
    color: #005cc5;
    font-weight: 700
}

.hljs-bullet {
    color: #735c0f
}

.hljs-emphasis {
    color: #24292e;
    font-style: italic
}

.hljs-strong {
    color: #24292e;
    font-weight: 700
}

.hljs-addition {
    color: #22863a;
    background-color: #f0fff4
}

.hljs-deletion {
    color: #b31d28;
    background-color: #ffeef0
}

`;

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
