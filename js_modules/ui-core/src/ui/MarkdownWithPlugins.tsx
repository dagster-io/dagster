import clsx from 'clsx';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import rehypeSanitize, {defaultSchema} from 'rehype-sanitize';
import remarkBreaks from 'remark-breaks';
import remarkGfm from 'remark-gfm';
import 'highlight.js/styles/github.css';

import styles from './css/MarkdownWithPlugins.module.css';

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
  softBreaks?: boolean;
}

export const MarkdownWithPlugins = ({softBreaks, ...props}: Props) => {
  return (
    <ReactMarkdown
      {...props}
      className={clsx('dagster-markdown', styles.dagsterMarkdown)}
      remarkPlugins={softBreaks ? [remarkBreaks, remarkGfm] : [remarkGfm]}
      rehypePlugins={[
        [rehypeHighlight, {ignoreMissing: true}],
        [rehypeSanitize, sanitizeConfig],
      ]}
    />
  );
};

// eslint-disable-next-line import/no-default-export
export default MarkdownWithPlugins;
