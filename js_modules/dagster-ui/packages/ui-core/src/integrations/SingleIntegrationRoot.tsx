import {
  Box,
  Heading,
  Icon,
  NonIdealState,
  PageHeader,
  SpinnerWithText,
} from '@dagster-io/ui-components';
import {useEffect, useState} from 'react';
import {Link, useParams} from 'react-router-dom';

import {IntegrationPage} from './IntegrationPage';
import {INTEGRATIONS_HOSTNAME} from './constants';
import {IntegrationConfig} from './types';
import {AnchorButton} from '../ui/AnchorButton';

export const SingleIntegrationRoot = () => {
  const {integrationName} = useParams<{integrationName: string}>();
  const [loading, setLoading] = useState(true);
  const [integration, setIntegration] = useState<IntegrationConfig | null>(null);

  useEffect(() => {
    const fetchIntegration = async () => {
      const url = `${INTEGRATIONS_HOSTNAME}/api/integrations/${integrationName}.json`;
      const res = await fetch(url);
      const data = await res.json();
      setIntegration(data);
      setLoading(false);
    };
    fetchIntegration();
  }, [integrationName]);

  const content = () => {
    if (loading) {
      return (
        <Box padding={64} flex={{direction: 'column', gap: 12, alignItems: 'center'}}>
          <SpinnerWithText label="Loading integration…" />
        </Box>
      );
    }

    if (!integration) {
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

    return <IntegrationPage integration={integration} />;
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader
        title={
          <Heading>
            <Box flex={{direction: 'row', gap: 8}}>
              <Link to="/integrations">Integrations Marketplace</Link>
              {integration?.frontmatter ? (
                <>
                  <span> / </span>
                  <div>{integration.frontmatter.name}</div>
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
