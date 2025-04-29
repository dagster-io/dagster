import {Box, Button, Icon} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {IntegrationIcon} from './IntegrationIcon';
import {BuiltByDagsterLabs, IntegrationTag, IntegrationTags} from './IntegrationTag';
import styles from './css/IntegrationTopcard.module.css';
import {IntegrationFrontmatter} from './types';

export const IntegrationTopcard = ({integration}: {integration: IntegrationFrontmatter}) => {
  const {id, name, title, tags, logoFilename, pypi, source} = integration;

  return (
    <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
      <Link
        to={`/integrations/${id}`}
        className={styles.itemLink}
        onClick={(e) => e.stopPropagation()}
      >
        <Box flex={{direction: 'row', gap: 16, alignItems: 'flex-start'}}>
          <IntegrationIcon name={name} logoFilename={logoFilename} />
          <Box
            flex={{direction: 'column', gap: 4, justifyContent: 'center'}}
            style={{minHeight: 48}}
          >
            <div style={{fontSize: 16, fontWeight: 600}}>{name || title}</div>
            {tags.includes(IntegrationTag.DagsterSupported) ? <BuiltByDagsterLabs /> : null}
          </Box>
        </Box>
      </Link>
      <Box flex={{direction: 'row', gap: 16, alignItems: 'center'}}>
        <IntegrationTags tags={tags} />
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
        </Box>
      </Box>
    </Box>
  );
};
