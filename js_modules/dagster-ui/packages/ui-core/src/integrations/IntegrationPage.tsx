import {Body, Box, Colors, Heading, PageHeader} from '@dagster-io/ui-components';
import {useLayoutEffect, useRef, useState} from 'react';
import ReactMarkdown from 'react-markdown';
import {CodeComponent} from 'react-markdown/lib/ast-to-react';
import {Link} from 'react-router-dom';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';

import {IntegrationIcon} from './IntegrationIcon';
import {CopyIconButton} from '../ui/CopyButton';
import styles from './css/IntegrationPage.module.css';
import {IntegrationConfig} from './types';

interface Props {
  integration: IntegrationConfig;
}

export const IntegrationPage = ({integration}: Props) => {
  const {
    frontmatter: {name, title, excerpt},
    logo,
    content,
  } = integration;

  return (
    <div>
      <PageHeader
        title={
          <Heading>
            <Box flex={{direction: 'row', gap: 8}}>
              <Link to="/integrations">Integrations Marketplace</Link>
              <span> / </span>
              <div>{title}</div>
            </Box>
          </Heading>
        }
      />
      <Box
        padding={{vertical: 24}}
        flex={{direction: 'column', gap: 24}}
        style={{width: '1100px', margin: '0 auto'}}
      >
        <Box flex={{direction: 'row', gap: 12, alignItems: 'flex-start'}}>
          <IntegrationIcon name={name} logo={logo} />
          <Box flex={{direction: 'column', gap: 2}} margin={{top: 4}}>
            <div style={{fontSize: 18, fontWeight: 600}}>{title}</div>
            <Body color={Colors.textLight()}>{excerpt}</Body>
          </Box>
        </Box>
        <div className={styles.markdownOutput}>
          <ReactMarkdown
            className={styles.integrationPage}
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[[rehypeHighlight, {ignoreMissing: true}]]}
            components={{
              code: Code,
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </Box>
    </div>
  );
};

const Code: CodeComponent = (props) => {
  const {children, className, ...rest} = props;
  const codeRef = useRef<HTMLElement>(null);
  const [value, setValue] = useState('');

  useLayoutEffect(() => {
    setValue(codeRef.current?.textContent?.trim() ?? '');
  }, [children]);

  return (
    <div className={styles.codeBlock}>
      <code className={className} {...rest} ref={codeRef}>
        {children}
      </code>
      <div className={styles.copyButton}>
        <CopyIconButton value={value} iconSize={16} iconColor={Colors.accentPrimary()} />
      </div>
    </div>
  );
};
