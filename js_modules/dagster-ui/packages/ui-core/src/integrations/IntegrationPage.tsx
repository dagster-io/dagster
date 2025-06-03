import {Body2, Box} from '@dagster-io/ui-components';
import bash from 'highlight.js/lib/languages/bash';
import yaml from 'highlight.js/lib/languages/yaml';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';
import rehypeSlug from 'rehype-slug';
import remarkDirective from 'remark-directive';
import remarkGfm from 'remark-gfm';

import {IntegrationTopcard} from './IntegrationTopcard';
import {
  MDXComponents,
  prependInstallationSection,
  replaceFrontmatterExpressions,
} from './MarkdownSupport';
import styles from './css/IntegrationPage.module.css';
import {IntegrationConfig} from './types';
import {useDOMTableOfContents} from './useDOMTableOfContents';

interface Props {
  integration: IntegrationConfig;
}

export const IntegrationPage = ({integration}: Props) => {
  const {frontmatter} = integration;
  const {markdownRef, tableOfContents} = useDOMTableOfContents();

  let content = integration.content;
  content = replaceFrontmatterExpressions(content, frontmatter);
  content = prependInstallationSection(content, frontmatter);

  return (
    <Box padding={{vertical: 24}} flex={{gap: 48, alignItems: 'flex-start'}}>
      <Box flex={{direction: 'column', gap: 12}} style={{minWidth: 0}}>
        <IntegrationTopcard integration={frontmatter} />

        <div
          className={styles.markdownOutput}
          ref={(ref) => {
            markdownRef.current = ref;
          }}
        >
          <ReactMarkdown
            className={styles.integrationPage}
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
        </div>
      </Box>
      <Box
        border="left"
        padding={{left: 24, vertical: 4}}
        style={{
          minWidth: '15vw',
          position: 'sticky',
          overflowY: 'auto',
          overflowX: 'hidden',
          maxHeight: 'calc(100vh - 148px)',
          top: 24,
        }}
      >
        {tableOfContents.map((heading, idx) => (
          <a href={`#${heading.id}`} key={`${heading.id}-${idx}`}>
            <div style={{paddingLeft: (heading.level - 1) * 12, paddingBottom: 4}}>
              <Body2>{heading.label}</Body2>
            </div>
          </a>
        ))}
      </Box>
    </Box>
  );
};
