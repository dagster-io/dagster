import {Colors} from '@dagster-io/ui-components';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import rehypeSanitize, {defaultSchema} from 'rehype-sanitize';
import gfm from 'remark-gfm';
import {createGlobalStyle} from 'styled-components';
import 'highlight.js/styles/github.css';

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
.hljs-doctag,.hljs-keyword,.hljs-meta .hljs-keyword,.hljs-template-tag,.hljs-template-variable,.hljs-type,.hljs-variable.language_ {
    color: ${Colors.accentRed()}
}

.hljs-title,.hljs-title.class_,.hljs-title.class_.inherited__,.hljs-title.function_ {
    color: ${Colors.dataVizBlurple()}
}

.hljs-attr,.hljs-attribute,.hljs-literal,.hljs-meta,.hljs-number,.hljs-operator,.hljs-selector-attr,.hljs-selector-class,.hljs-selector-id,.hljs-variable {
    color: ${Colors.dataVizBlue()}
}

.hljs-meta .hljs-string,.hljs-regexp,.hljs-string {
    color: ${Colors.accentBlue()}
}

.hljs-built_in,.hljs-symbol {
    color: ${Colors.dataVizOrange()}
}

.hljs-code,.hljs-comment,.hljs-formula {
    color: ${Colors.dataVizGray()}
}

.hljs-name,.hljs-quote,.hljs-selector-pseudo,.hljs-selector-tag {
    color: ${Colors.dataVizGreen()}
}
`;

interface Props {
  children: string;
}

export const MarkdownWithPlugins = (props: Props) => {
  return (
    <>
      <GlobalStyle />
      <ReactMarkdown
        {...props}
        remarkPlugins={[gfm]}
        rehypePlugins={[rehypeHighlight, [rehypeSanitize, sanitizeConfig]]}
      />
    </>
  );
};

// eslint-disable-next-line import/no-default-export
export default MarkdownWithPlugins;
