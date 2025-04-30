import {Box} from '@dagster-io/ui-components';
import bash from 'highlight.js/lib/languages/bash';
import yaml from 'highlight.js/lib/languages/yaml';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';
import remarkDirective from 'remark-directive';
import remarkGfm from 'remark-gfm';

import {IntegrationTopcard} from './IntegrationTopcard';
import {MDXComponents} from './MarkdownSupport';
import styles from './css/IntegrationPage.module.css';
import {IntegrationConfig} from './types';

interface Props {
  integration: IntegrationConfig;
}

export const IntegrationPage = ({integration}: Props) => {
  const {frontmatter, content} = integration;

  return (
    <div>
      <Box padding={{vertical: 24}} flex={{direction: 'column', gap: 12}}>
        <IntegrationTopcard integration={frontmatter} />

        <div className={styles.markdownOutput}>
          <ReactMarkdown
            className={styles.integrationPage}
            components={MDXComponents}
            remarkPlugins={[remarkDirective, remarkGfm]}
            remarkRehypeOptions={{allowDangerousHtml: true}}
            rehypePlugins={[
              rehypeRaw,
              [rehypeHighlight, {ignoreMissing: true, languages: [bash, yaml]}],
            ]}
          >
            {content}
          </ReactMarkdown>
        </div>
      </Box>
    </div>
  );
};
