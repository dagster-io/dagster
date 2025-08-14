import {Box, SpinnerWithText} from '@dagster-io/ui-components';

import {useQuery} from '../apollo-client';
import {CodeLocationDefsStateComparison} from './CodeLocationDefsStateComparison';
import {CODE_LOCATION_DEFS_STATE_QUERY} from './CodeLocationDefsStateQuery';
import {CodeLocationOverviewSectionHeader} from './CodeLocationOverviewSectionHeader';

interface Props {
  locationName: string;
}

export const CodeLocationDefsStateComparisonSection = ({locationName}: Props) => {
  const {data, loading, error} = useQuery(CODE_LOCATION_DEFS_STATE_QUERY, {
    variables: {locationName},
    fetchPolicy: 'cache-and-network',
  });

  if (loading && !data) {
    return (
      <Box padding={64} flex={{direction: 'row', justifyContent: 'center'}}>
        <SpinnerWithText label="Loading defs state comparison…" />
      </Box>
    );
  }

  if (error) {
    return null; // Silently fail if there's an error
  }

  const latestDefsStateInfo = data?.latestDefsStateInfo || null;
  const defsStateInfo =
    data?.workspaceLocationEntryOrError?.__typename === 'WorkspaceLocationEntry'
      ? data.workspaceLocationEntryOrError.defsStateInfo
      : null;

  // Only show the section if we have data to compare
  if (!latestDefsStateInfo || !defsStateInfo) {
    return null;
  }

  // Don't show the section if there are no versions available in the current state
  if (!defsStateInfo.keyStateInfo || defsStateInfo.keyStateInfo.length === 0) {
    return null;
  }

  return (
    <>
      <CodeLocationOverviewSectionHeader label="Defs State Versions" />
      <CodeLocationDefsStateComparison
        latestDefsStateInfo={latestDefsStateInfo}
        defsStateInfo={defsStateInfo}
      />
    </>
  );
};
