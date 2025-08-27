import {Box, Button, Icon} from '@dagster-io/ui-components';
import React from 'react';
import {Link} from 'react-router-dom';

import {IntegrationIcon} from './IntegrationIcon';
import {
  BuiltByDagsterLabs,
  IntegrationTag,
  IntegrationTags,
  PrivateIntegration,
} from './IntegrationTag';
import styles from './css/IntegrationTopcard.module.css';
import {IntegrationFrontmatter} from './types';

export const IntegrationTopcard = ({
  integration,
  children,
}: {
  integration: IntegrationFrontmatter;
  children?: React.ReactNode;
}) => {
  const {id, name, title, tags, logo, logoFilename, pypi, source, isPrivate} = integration;

  return (
    <Box flex={{direction: 'row', gap: 16, justifyContent: 'space-between'}}>
      <Link
        to={`/integrations/${id}`}
        className={styles.itemLink}
        onClick={(e) => e.stopPropagation()}
      >
        <Box flex={{direction: 'row', gap: 16, alignItems: 'flex-start'}}>
          <IntegrationIcon name={name} content={logo || logoFilename} />
          <Box
            flex={{direction: 'column', gap: 4, justifyContent: 'center'}}
            style={{minHeight: 48}}
          >
            <div style={{fontSize: 16, fontWeight: 600}}>{name || title}</div>
            {tags.includes(IntegrationTag.DagsterSupported) ? <BuiltByDagsterLabs /> : null}
            {isPrivate ? <PrivateIntegration /> : null}
          </Box>
        </Box>
      </Link>
      <Box flex={{direction: 'row', gap: 16, alignItems: 'center'}}>
        <Box
          flex={{direction: 'row', gap: 8, wrap: 'wrap', justifyContent: 'flex-end'}}
          style={{minWidth: 0}}
        >
          <IntegrationTags tags={tags} />
        </Box>
        <Box flex={{direction: 'row', gap: 8}}>
          {pypi ? (
            <a
              href={pypi}
              target="_blank"
              rel="noreferrer"
              className={styles.externalLink}
              onClick={(e) => e.stopPropagation()}
            >
              <Button icon={<Icon name="python" size={16} />} />
            </a>
          ) : null}
          {source ? (
            <a
              href={source}
              target="_blank"
              rel="noreferrer"
              className={styles.externalLink}
              onClick={(e) => e.stopPropagation()}
            >
              <Button icon={<Icon name="github" size={16} />} />
            </a>
          ) : null}
          {children}
        </Box>
      </Box>
    </Box>
  );
};
