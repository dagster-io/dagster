import {Box, SpinnerWithText} from '@dagster-io/ui-components';

import {useQuery} from '../apollo-client';
import {CodeLocationDefsStateComparison} from './CodeLocationDefsStateComparison';
import {CODE_LOCATION_DEFS_STATE_QUERY} from './CodeLocationDefsStateQuery';
import {CodeLocationOverviewSectionHeader} from './CodeLocationOverviewSectionHeader';
import {
  CodeLocationDefsStateQuery,
  CodeLocationDefsStateQueryVariables,
} from './types/CodeLocationDefsStateQuery.types';

interface Props {
  locationName: string;
}

export const CodeLocationDefsStateComparisonSection = ({locationName}: Props) => {
  const {data, loading} = useQuery<CodeLocationDefsStateQuery, CodeLocationDefsStateQueryVariables>(
    CODE_LOCATION_DEFS_STATE_QUERY,
    {
      variables: {locationName},
      fetchPolicy: 'cache-and-network',
    },
  );

  if (loading && !data) {
    return (
      <Box padding={64} flex={{direction: 'row', justifyContent: 'center'}}>
        <SpinnerWithText label="Loading defs state comparison…" />
      </Box>
    );
  }

  const defsStateInfo =
    data?.workspaceLocationEntryOrError?.__typename === 'WorkspaceLocationEntry'
      ? data.workspaceLocationEntryOrError.defsStateInfo
      : null;

  // Don't show the section if there are no versions available in the current state
  if (!defsStateInfo?.keyStateInfo || defsStateInfo.keyStateInfo.length === 0) {
    return null;
  }

  const latestDefsStateInfo = data?.latestDefsStateInfo ?? null;
  return (
    <>
      <CodeLocationOverviewSectionHeader label="Defs state versions" />
      <CodeLocationDefsStateComparison
        latestDefsStateInfo={latestDefsStateInfo}
        defsStateInfo={defsStateInfo}
      />
    </>
  );
};
