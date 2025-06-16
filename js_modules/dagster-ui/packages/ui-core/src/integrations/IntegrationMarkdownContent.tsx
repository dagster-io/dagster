import bash from 'highlight.js/lib/languages/bash';
import yaml from 'highlight.js/lib/languages/yaml';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';
import rehypeSlug from 'rehype-slug';
import remarkDirective from 'remark-directive';
import remarkGfm from 'remark-gfm';

import {
  MDXComponents,
  prependInstallationSection,
  replaceFrontmatterExpressions,
} from './MarkdownSupport';
import {IntegrationConfig} from './types';

export const IntegrationMarkdownContent = ({
  integration,
  className,
}: {
  integration: IntegrationConfig;
  className?: string;
}) => {
  const {frontmatter} = integration;

  let content = integration.content;
  content = replaceFrontmatterExpressions(content, frontmatter);
  content = prependInstallationSection(content, frontmatter);
  return (
    <ReactMarkdown
      className={className}
      components={MDXComponents}
      remarkPlugins={[remarkDirective, remarkGfm]}
      remarkRehypeOptions={{allowDangerousHtml: true}}
      rehypePlugins={[
        rehypeRaw,
        [rehypeSlug, {prefix: 'docs-'}],
        [rehypeHighlight, {ignoreMissing: true, languages: [bash, yaml]}],
      ]}
    >
      {content}
    </ReactMarkdown>
  );
};
