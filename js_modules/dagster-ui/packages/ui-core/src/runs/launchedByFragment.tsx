import {gql} from '../apollo-client';

export const LAUNCHED_BY_FRAGMENT = gql`
  fragment LaunchedByFragment on LaunchedBy {
    kind
    tag {
      key
      value
    }
  }
`;
