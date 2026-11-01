import {RUNS_FEED_ENTRY_FRAGMENT} from './RunsFeedFragments';
import {gql} from '../../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';

export const RUNS_FEED_QUERY = gql`
  query RunsFeedQuery($limit: Int!, $cursor: String, $filter: RunsFilter, $view: RunsFeedView!) {
    runsFeedOrError(limit: $limit, cursor: $cursor, filter: $filter, view: $view) {
      ... on RunsFeedConnection {
        cursor
        hasMore
        results {
          ...RunsFeedEntryFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${RUNS_FEED_ENTRY_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
