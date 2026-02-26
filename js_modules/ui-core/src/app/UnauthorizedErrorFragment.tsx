import {gql} from '../apollo-client';

export const UNAUTHORIZED_ERROR_FRAGMENT = gql`
  fragment UnauthorizedErrorFragment on UnauthorizedError {
    message
  }
`;
