import {gql} from '@apollo/client';

import {RUN_FRAGMENT} from '../RunFragments';

export const RUN_ACTION_BUTTONS_TEST_QUERY = gql`
  query RunActionButtonsTestQuery {
    pipelineRunOrError(runId: "foo") {
      ... on Run {
        id
        parentPipelineSnapshotId
        ...RunFragment
      }
    }
  }

  ${RUN_FRAGMENT}
`;
