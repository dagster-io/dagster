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
import {useIntegrationsProvider} from 'shared/integrations/useIntegrationsProvider.oss';

import {SingleIntegrationPage} from './SingleIntegrationPage';
import {IntegrationConfig} from './types';
import {useTrackPageView} from '../app/analytics';
import {AnchorButton} from '../ui/AnchorButton';

export const SingleIntegrationRoot = () => {
  useTrackPageView();
  const {integrationId} = useParams<{integrationId: string}>();
  const [loading, setLoading] = useState(true);
  const [integration, setIntegration] = useState<IntegrationConfig | null>(null);
  const provider = useIntegrationsProvider();
  const {fetchIntegrationDetails} = provider;

  useEffect(() => {
    const load = async () => {
      setIntegration(await fetchIntegrationDetails(integrationId));
      setLoading(false);
    };
    load();
  }, [fetchIntegrationDetails, integrationId]);

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

    return <SingleIntegrationPage integration={integration} provider={provider} />;
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
