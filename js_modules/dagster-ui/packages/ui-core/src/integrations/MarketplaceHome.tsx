import {Box, Button, Colors, Heading, Icon, Tag, TextInput} from '@dagster-io/ui-components';
import {useState} from 'react';
import {Link} from 'react-router-dom';

import {IntegrationIcon} from './IntegrationIcon';
import {
  IntegrationTag,
  IntegrationTagIcon,
  IntegrationTagKeys,
  IntegrationTagLabel,
} from './IntegrationTag';
import styles from './css/MarketplaceHome.module.css';
import {IntegrationFrontmatter} from './types';
interface Props {
  integrations: IntegrationFrontmatter[];
}

export const MarketplaceHome = (props: Props) => {
  const {integrations} = props;
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<IntegrationTag | null>(null);

  const filteredByTag = integrations.filter((integration) => {
    const {tags} = integration;
    return filters === null || tags.some((tag) => filters === tag);
  });

  const filteredIntegrations = filteredByTag.filter((integration) => {
    return integration.name.toLowerCase().includes(searchQuery.toLowerCase());
  });

  return (
    <Box flex={{direction: 'column', gap: 12}}>
      <Box margin={{bottom: 8}}>
        <Heading>Integrations Marketplace</Heading>
      </Box>
      <TextInput
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search for integrations"
        icon="search"
      />
      <Box
        flex={{direction: 'row', gap: 12, alignItems: 'center', wrap: 'wrap'}}
        margin={{bottom: 12}}
      >
        <div style={{fontSize: 16}}>Filters</div>
        {Object.values(IntegrationTag).map((tag) => (
          <Button
            key={tag}
            icon={<Icon name={IntegrationTagIcon[tag]} />}
            onClick={() => setFilters(filters === tag ? null : tag)}
            style={{backgroundColor: filters === tag ? Colors.backgroundBlue() : 'transparent'}}
          >
            {IntegrationTagLabel[tag]}
          </Button>
        ))}
      </Box>
      <Box flex={{direction: 'column', gap: 12}}>
        {filteredIntegrations.map((integration) => {
          const {id, name, title, tags, excerpt, logoFilename, pypiUrl, repoUrl} = integration;
          return (
            <Box
              padding={{top: 12, bottom: 16, horizontal: 12}}
              border="all"
              style={{borderRadius: 8, overflow: 'hidden'}}
              className={styles.itemCard}
              key={id}
            >
              <Link to={`/integrations/${id}`} className={styles.itemLink}>
                <Box flex={{direction: 'row', gap: 16, alignItems: 'flex-start'}}>
                  <IntegrationIcon name={name} logoFilename={logoFilename} />
                  <Box flex={{direction: 'column', gap: 4}}>
                    <Box
                      flex={{
                        direction: 'row',
                        alignItems: 'center',
                        justifyContent: 'flex-start',
                        gap: 12,
                      }}
                      padding={{top: 12}}
                    >
                      <div style={{fontSize: 16, fontWeight: 600}}>{name || title}</div>
                      {tags.includes(IntegrationTag.DagsterSupported) ? (
                        <Box
                          flex={{direction: 'row', alignItems: 'center', gap: 4}}
                          style={{fontSize: 12, color: Colors.textLight()}}
                        >
                          <Icon name="shield_check" size={12} color={Colors.textLight()} />
                          Built by Dagster Labs
                        </Box>
                      ) : null}
                    </Box>
                    <div className={styles.excerpt}>{excerpt}</div>
                  </Box>
                </Box>
              </Link>
              <Box flex={{direction: 'row', gap: 12}} className={styles.itemTags}>
                {tags
                  .filter((tag): tag is IntegrationTag => IntegrationTagKeys.includes(tag))
                  .map((tag) => {
                    const icon = IntegrationTagIcon[tag];
                    return (
                      <Tag key={tag} icon={icon ?? undefined}>
                        {IntegrationTagLabel[tag]}
                      </Tag>
                    );
                  })}
                {pypiUrl ? (
                  <a
                    href={pypiUrl}
                    target="_blank"
                    rel="noreferrer"
                    className={styles.externalLink}
                  >
                    <Icon name="python" size={12} />
                    pypi
                    <Icon name="open_in_new" size={12} />
                  </a>
                ) : null}
                {repoUrl ? (
                  <a
                    href={repoUrl}
                    target="_blank"
                    rel="noreferrer"
                    className={styles.externalLink}
                  >
                    <Icon name="github" size={12} />
                    repo
                    <Icon name="open_in_new" size={12} />
                  </a>
                ) : null}
              </Box>
            </Box>
          );
        })}
      </Box>
    </Box>
  );
};
