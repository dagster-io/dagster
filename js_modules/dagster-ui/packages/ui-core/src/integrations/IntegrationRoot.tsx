import {Box, Heading, Icon, NonIdealState, PageHeader} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {Link, useParams} from 'react-router-dom';

import {IntegrationPage} from './IntegrationPage';
import * as allIntegrations from './__generated__';
import {AnchorButton} from '../ui/AnchorButton';

export const IntegrationRoot = () => {
  const {integrationName} = useParams<{integrationName: string}>();

  const matchingIntegration = useMemo(() => {
    const match = Object.entries(allIntegrations).find(
      ([key]) => key.toLocaleLowerCase() === integrationName.toLocaleLowerCase(),
    );
    return match ? match[1] : null;
  }, [integrationName]);

  const content = () => {
    if (!matchingIntegration) {
      return (
        <Box padding={64} flex={{direction: 'column', gap: 12}}>
          <NonIdealState
            icon="search"
            title="Integration not found"
            description="This integration could not be found."
            action={
              <AnchorButton to="/integrations" icon={<Icon name="arrow_back" />}>
                Back to Integrations Marketplace
              </AnchorButton>
            }
          />
        </Box>
      );
    }

    return <IntegrationPage integration={matchingIntegration} />;
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader
        title={
          <Heading>
            <Box flex={{direction: 'row', gap: 8}}>
              <Link to="/integrations">Integrations Marketplace</Link>
              {matchingIntegration ? (
                <>
                  <span> / </span>
                  <div>{matchingIntegration?.frontmatter.name}</div>
                </>
              ) : null}
            </Box>
          </Heading>
        }
      />
      <div style={{flex: 1, overflowY: 'auto'}}>
        <div
          style={{
            width: '80vw',
            maxWidth: '1100px',
            minWidth: '900px',
            margin: '0 auto',
          }}
        >
          {content()}
        </div>
      </div>
    </Box>
  );
};
