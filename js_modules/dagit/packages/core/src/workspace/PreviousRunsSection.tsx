import {gql} from '@apollo/client';
import * as React from 'react';

import {RunTable, RUN_TABLE_RUN_FRAGMENT} from '../runs/RunTable';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Subheading} from '../ui/Text';

import {PreviousRunsFragment} from './types/PreviousRunsFragment';

export const PreviousRunsSection: React.FC<{
  loading: boolean;
  data: PreviousRunsFragment | null | undefined;
  highlightedIds?: string[];
}> = ({loading, data, highlightedIds}) => {
  const content = () => {
    if (loading) {
      return <Box margin={{top: 8}}>Loading...</Box>;
    }
    if (!data || data.__typename !== 'Runs') {
      return <Box margin={{top: 8}}>Error!</Box>;
    }
    const runs = data?.results;
    return <RunTable onSetFilter={() => {}} runs={runs} highlightedIds={highlightedIds} />;
  };

  return (
    <>
      <Box
        padding={{vertical: 16, horizontal: 24}}
        flex={{direction: 'row'}}
        border={{side: 'horizontal', width: 1, color: ColorsWIP.KeylineGray}}
      >
        <Subheading>Latest runs</Subheading>
      </Box>
      <div style={{color: ColorsWIP.Gray400}}>{content()}</div>
    </>
  );
};

export const PREVIOUS_RUNS_FRAGMENT = gql`
  fragment PreviousRunsFragment on RunsOrError {
    __typename
    ... on Runs {
      results {
        id
        ... on PipelineRun {
          ...RunTableRunFragment
        }
      }
    }
  }
  ${RUN_TABLE_RUN_FRAGMENT}
`;
