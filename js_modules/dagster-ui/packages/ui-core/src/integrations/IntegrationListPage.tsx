import {Box, Button, Colors, Heading, Icon, Page, TextInput} from '@dagster-io/ui-components';
import {useHistory} from 'react-router-dom';
import {IntegrationsProvider} from 'shared/integrations/useIntegrationsProvider.oss';

import {AddIntegrationButton} from './AddIntegrationButton';
import {IntegrationTag, IntegrationTagIcon, IntegrationTagLabel} from './IntegrationTag';
import {IntegrationTopcard} from './IntegrationTopcard';
import styles from './css/MarketplaceHome.module.css';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';

const IntegrationTagValues = new Set(Object.values(IntegrationTag));

export const IntegrationListPage = ({provider}: {provider: IntegrationsProvider}) => {
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
              .filter((k): k is IntegrationTag => IntegrationTagValues.has(k as IntegrationTag))
          : null;
      }
      return null;
    },
  });

  const filteredByTag = provider.integrations.filter((integration) => {
    const {tags} = integration;
    return filters === null || filters.every((filter) => tags.includes(filter));
  });

  const lowerCaseSearchQuery = searchQuery.toLowerCase();
  const filteredIntegrations = filteredByTag.filter((integration) => {
    return integration.name.toLowerCase().includes(lowerCaseSearchQuery);
  });

  // Note: `overflowY: scroll` prevents the page content from jumping slightly when you
  // apply filters and the viewport height no longer requires a scrollbar.
  return (
    <Page style={{backgroundColor: Colors.backgroundLight(), overflowY: 'scroll'}}>
      <Box
        padding={{vertical: 32}}
        style={{width: '80vw', maxWidth: '1200px', minWidth: '800px', margin: '0 auto'}}
      >
        <Box flex={{direction: 'column', gap: 12}}>
          <Box margin={{bottom: 8}} flex={{justifyContent: 'space-between'}}>
            <Heading>Integrations Marketplace</Heading>
            <AddIntegrationButton provider={provider} />
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
      </Box>
    </Page>
  );
};
