import {gql} from '@apollo/client';
import * as React from 'react';

import {RunTable, RUN_TABLE_RUN_FRAGMENT} from '../runs/RunTable';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {PageSection} from '../ui/PageSection';
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
    if (!data || data.__typename !== 'PipelineRuns') {
      return <Box margin={{top: 8}}>Error!</Box>;
    }
    const runs = data?.results;
    return <RunTable onSetFilter={() => {}} runs={runs} highlightedIds={highlightedIds} />;
  };

  return (
    <PageSection>
      <Box padding={{vertical: 16, horizontal: 24}} flex={{direction: 'row'}}>
        <Subheading>Latest runs</Subheading>
      </Box>
      <div style={{color: ColorsWIP.Gray400}}>{content()}</div>
    </PageSection>
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
  ${RUN_TABLE_RUN_FRAGMENT}
`;
