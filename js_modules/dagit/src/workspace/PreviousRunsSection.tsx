import {gql} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import * as React from 'react';

import {RunTable} from 'src/runs/RunTable';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {Subheading} from 'src/ui/Text';
import {PreviousRunsFragment} from 'src/workspace/types/PreviousRunsFragment';

export const PreviousRunsSection: React.FC<{
  loading: boolean;
  data: PreviousRunsFragment | null | undefined;
  highlightedIds?: string[];
}> = ({loading, data, highlightedIds}) => {
  const content = () => {
    if (loading) {
      return <Box margin={{top: 8}}>Loading...</Box>;
    }
    if (!data || data.__typename !== 'PipelineRuns') {
      return <Box margin={{top: 8}}>Error!</Box>;
    }
    const runs = data?.results;
    return <RunTable onSetFilter={() => {}} runs={runs} highlightedIds={highlightedIds} />;
  };

  return (
    <Group direction="column" spacing={4}>
      <Box
        padding={{bottom: 12}}
        border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
        flex={{direction: 'row'}}
      >
        <Subheading>Latest runs</Subheading>
      </Box>
      <div style={{color: Colors.GRAY3}}>{content()}</div>
    </Group>
  );
};

export const PREVIOUS_RUNS_FRAGMENT = gql`
  fragment PreviousRunsFragment on PipelineRunsOrError {
    __typename
    ... on PipelineRuns {
      results {
        id
        ... on PipelineRun {
          ...RunTableRunFragment
        }
      }
    }
  }
  ${RunTable.fragments.RunTableRunFragment}
`;
