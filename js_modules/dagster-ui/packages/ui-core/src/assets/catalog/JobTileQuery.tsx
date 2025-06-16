import {gql} from '../../apollo-client';

export const JOB_TILE_QUERY = gql`
  query JobTileQuery($pipelineSelector: PipelineSelector!) {
    pipelineOrError(params: $pipelineSelector) {
      ... on Pipeline {
        id
        runs(limit: 1) {
          id
          runId
          runStatus
          startTime
        }
      }
    }
  }
`;
