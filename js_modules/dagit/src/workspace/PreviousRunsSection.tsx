import {gql} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import * as React from 'react';

import {RunTable} from 'src/runs/RunTable';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {Subheading} from 'src/ui/Text';
import {PreviousRunsFragment} from 'src/workspace/types/PreviousRunsFragment';

interface Props {
  loading: boolean;
  data: PreviousRunsFragment | null | undefined;
}

export const PreviousRunsSection = (props: Props) => {
  const {loading, data} = props;

  const content = () => {
    if (loading) {
      return <Box margin={{top: 8}}>Loading...</Box>;
    }
    if (!data || data.__typename !== 'PipelineRuns') {
      return <Box margin={{top: 8}}>Error!</Box>;
    }
    const runs = data?.results;
    return <RunTable onSetFilter={() => {}} runs={runs} />;
  };

  return (
    <Group direction="vertical" spacing={4}>
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
