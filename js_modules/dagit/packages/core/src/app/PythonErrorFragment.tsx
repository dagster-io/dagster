import {gql} from '@apollo/client';

export const PYTHON_ERROR_FRAGMENT = gql`
  fragment PythonErrorFragment on PythonError {
    __typename
    message
    stack
    errorChain {
      ...PythonErrorChain
    }
  }

  fragment PythonErrorChain on ErrorChainLink {
    isExplicitLink
    error {
      message
      stack
    }
  }
`;
