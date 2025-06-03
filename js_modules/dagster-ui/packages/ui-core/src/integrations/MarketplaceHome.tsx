import {Box, Button, Colors, Heading, Icon, TextInput} from '@dagster-io/ui-components';
import {useHistory} from 'react-router-dom';

import {IntegrationTag, IntegrationTagIcon, IntegrationTagLabel} from './IntegrationTag';
import {IntegrationTopcard} from './IntegrationTopcard';
import styles from './css/MarketplaceHome.module.css';
import {IntegrationFrontmatter} from './types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
interface Props {
  integrations: IntegrationFrontmatter[];
}

export const MarketplaceHome = (props: Props) => {
  const {integrations} = props;
  const history = useHistory();

  const [searchQuery, setSearchQuery] = useQueryPersistedState<string>({
    queryKey: 'search',
    defaults: {search: ''},
  });
  const [filters, setFilters] = useQueryPersistedState<IntegrationTag[] | null>({
    encode: (tags) => ({tags: tags?.length ? tags.join(',') : undefined}),
    decode: (qs) => {
      if (typeof qs.tags === 'string') {
        return qs.tags
          ? qs.tags
              .split(',')
              .filter((k) => Object.values(IntegrationTag).includes(k as IntegrationTag))
              .map((k) => k as IntegrationTag)
          : null;
      }
      return null;
    },
  });

  const filteredByTag = integrations.filter((integration) => {
    const {tags} = integration;
    return filters === null || filters.every((filter) => tags.includes(filter));
  });

  const filteredIntegrations = filteredByTag.filter((integration) => {
    return integration.name.toLowerCase().includes(searchQuery.toLowerCase());
  });

  return (
    <Box flex={{direction: 'column', gap: 12}}>
      <Box margin={{bottom: 8}}>
        <Heading>Integrations Marketplace</Heading>
      </Box>
      <div className={styles.searchInput}>
        <TextInput
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search for integrations"
          icon="search"
        />
      </div>
      <Box
        flex={{direction: 'row', gap: 12, alignItems: 'center', wrap: 'wrap'}}
        margin={{bottom: 12}}
      >
        <div style={{fontSize: 14}}>Filters</div>
        {Object.values(IntegrationTag).map((tag) => (
          <Button
            key={tag}
            icon={<Icon name={IntegrationTagIcon[tag]} />}
            onClick={() =>
              setFilters(
                filters?.includes(tag)
                  ? filters.filter((f) => f !== tag)
                  : [...(filters || []), tag],
              )
            }
            style={{
              backgroundColor: filters?.includes(tag) ? Colors.backgroundBlue() : 'transparent',
            }}
          >
            {IntegrationTagLabel[tag]}
          </Button>
        ))}
      </Box>
      <Box flex={{direction: 'column', gap: 12}}>
        {filteredIntegrations.map((integration) => {
          return (
            <Box
              border="all"
              padding={{vertical: 16, horizontal: 24}}
              style={{borderRadius: 8, overflow: 'hidden'}}
              className={styles.itemCard}
              key={integration.id}
              onClick={() => history.push(`/integrations/${integration.id}`)}
            >
              <IntegrationTopcard integration={integration} />
              <div className={styles.description}>{integration.description}</div>
            </Box>
          );
        })}
      </Box>
    </Box>
  );
};
