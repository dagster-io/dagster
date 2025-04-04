import {Body, Box, Colors} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {useLayoutEffect, useRef, useState} from 'react';
import ReactMarkdown from 'react-markdown';
import {Components} from 'react-markdown/lib/ast-to-react';
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
      <Box padding={{vertical: 24}} flex={{direction: 'column', gap: 12}}>
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
              a: Anchor,
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </Box>
    </div>
  );
};

const DOCS_ORIGIN = 'https://docs.dagster.io';

const Anchor: Components['a'] = (props) => {
  const {children, href, ...rest} = props;
  const finalHref = href?.startsWith('/') ? `${DOCS_ORIGIN}${href}` : href;
  return (
    <a href={finalHref} target="_blank" rel="noreferrer" {...rest}>
      {children}
    </a>
  );
};

const Code: Components['code'] = (props) => {
  const {children, className, inline, ...rest} = props;

  const codeRef = useRef<HTMLElement>(null);
  const [value, setValue] = useState('');

  useLayoutEffect(() => {
    setValue(codeRef.current?.textContent?.trim() ?? '');
  }, [children]);

  if (inline) {
    return (
      <code className={clsx(className, styles.inlineCode)} {...rest}>
        {children}
      </code>
    );
  }

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
