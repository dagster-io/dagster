import {gql} from '../apollo-client';

export const RUN_REQUEST_FRAGMENT = gql`
  fragment RunRequestFragment on RunRequest {
    runConfigYaml
    tags {
      key
      value
    }
    runKey
    jobName
    assetSelection {
      path
    }
    assetChecks {
      name
      assetKey {
        path
      }
    }
  }
`;
