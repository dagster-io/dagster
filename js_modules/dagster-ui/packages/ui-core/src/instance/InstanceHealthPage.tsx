import {Box, Colors, Heading, PageHeader, Subheading} from '@dagster-io/ui-components';
import {useContext} from 'react';

import {DaemonList} from './DaemonList';
import {INSTANCE_HEALTH_FRAGMENT} from './InstanceHealthFragment';
import {InstancePageContext} from './InstancePageContext';
import {InstanceTabs} from './InstanceTabs';
import {gql, useQuery} from '../apollo-client';
import {InstanceHealthQuery, InstanceHealthQueryVariables} from './types/InstanceHealthPage.types';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';

export const InstanceHealthPageContent = () => {
  useTrackPageView();
  useDocumentTitle('Daemons');

  const queryData = useQuery<InstanceHealthQuery, InstanceHealthQueryVariables>(
    INSTANCE_HEALTH_QUERY,
    {
      notifyOnNetworkStatusChange: true,
    },
  );
  const refreshState = useQueryRefreshAtInterval(queryData, FIFTEEN_SECONDS);
  const {loading, data} = queryData;

  const daemonContent = () => {
    if (loading && !data?.instance) {
      return (
        <Box padding={{horizontal: 24}} style={{color: Colors.textLight()}}>
          Loading…
        </Box>
      );
    }
    return data?.instance ? (
      <DaemonList daemonStatuses={data.instance.daemonHealth.allDaemonStatuses} />
    ) : null;
  };

  return (
    <div style={{overflowY: 'auto'}}>
      <Box
        padding={{vertical: 16, horizontal: 24}}
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
      >
        <Subheading>Daemon statuses</Subheading>
        <div>
          <QueryRefreshCountdown refreshState={refreshState} />
        </div>
      </Box>
      {daemonContent()}
    </div>
  );
};

export const InstanceHealthPage = () => {
  const {pageTitle} = useContext(InstancePageContext);
  return (
    <>
      <PageHeader title={<Heading>{pageTitle}</Heading>} tabs={<InstanceTabs tab="health" />} />
      <InstanceHealthPageContent />
    </>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default InstanceHealthPage;

const INSTANCE_HEALTH_QUERY = gql`
  query InstanceHealthQuery {
    instance {
      id
      ...InstanceHealthFragment
    }
  }

  ${INSTANCE_HEALTH_FRAGMENT}
`;
