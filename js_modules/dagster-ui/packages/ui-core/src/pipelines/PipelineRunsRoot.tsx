import {PipelineRunsFeedRoot} from './PipelineRunsFeedRoot';
import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {RUN_TABLE_RUN_FRAGMENT} from '../runs/RunTableRunFragment';
import {RunFilterTokenType} from '../runs/RunsFilterInput';
import {RepoAddress} from '../workspace/types';

const PAGE_SIZE = 25;
const ENABLED_FILTERS: RunFilterTokenType[] = [
  'status',
  'tag',
  'id',
  'created_date_before',
  'created_date_after',
];

interface Props {
  repoAddress?: RepoAddress;
}

export const PipelineRunsRoot = (props: Props) => {
  return <PipelineRunsFeedRoot {...props} />;
};

const PIPELINE_RUNS_ROOT_QUERY = gql`
  query PipelineRunsRootQuery($limit: Int, $cursor: String, $filter: RunsFilter!) {
    pipelineRunsOrError(limit: $limit, cursor: $cursor, filter: $filter) {
      ... on Runs {
        results {
          id
          ...RunTableRunFragment
        }
      }
      ... on InvalidPipelineRunsFilterError {
        message
      }
      ...PythonErrorFragment
    }
  }

  ${RUN_TABLE_RUN_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
