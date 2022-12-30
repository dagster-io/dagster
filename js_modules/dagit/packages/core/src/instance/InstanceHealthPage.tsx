import {useQuery} from '@apollo/client';
import {Box, Colors, PageHeader, Heading, Subheading} from '@dagster-io/ui';
import * as React from 'react';

import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {graphql} from '../graphql';

import {DaemonList} from './DaemonList';
import {InstancePageContext} from './InstancePageContext';
import {InstanceTabs} from './InstanceTabs';

export const InstanceHealthPage = () => {
  useTrackPageView();

  const {pageTitle} = React.useContext(InstancePageContext);
  const queryData = useQuery(INSTANCE_HEALTH_QUERY, {
    fetchPolicy: 'cache-and-network',
    notifyOnNetworkStatusChange: true,
  });
  const refreshState = useQueryRefreshAtInterval(queryData, FIFTEEN_SECONDS);
  const {loading, data} = queryData;

  const daemonContent = () => {
    if (loading && !data?.instance) {
      return (
        <Box padding={{horizontal: 24}} style={{color: Colors.Gray400}}>
          Loading…
        </Box>
      );
    }
    return data?.instance ? (
      <DaemonList daemonStatuses={data.instance.daemonHealth.allDaemonStatuses} />
    ) : null;
  };

  return (
    <>
      <PageHeader
        title={<Heading>{pageTitle}</Heading>}
        tabs={<InstanceTabs tab="health" refreshState={refreshState} />}
      />
      <Box padding={{vertical: 16, horizontal: 24}}>
        <Subheading>Daemon statuses</Subheading>
      </Box>
      {daemonContent()}
    </>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default InstanceHealthPage;

const INSTANCE_HEALTH_QUERY = graphql(`
  query InstanceHealthQuery {
    instance {
      ...InstanceHealthFragment
    }
  }
`);
