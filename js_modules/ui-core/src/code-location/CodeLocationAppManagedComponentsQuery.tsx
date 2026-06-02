import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';

export const APP_MANAGED_COMPONENT_FRAGMENT = gql`
  fragment AppManagedComponentFragment on AppManagedComponent {
    componentId
    componentType
    attributes
  }
`;

export const CODE_LOCATION_APP_MANAGED_COMPONENTS_QUERY = gql`
  query CodeLocationAppManagedComponentsQuery($locationName: String!) {
    appManagedComponentsForLocationOrError(locationName: $locationName) {
      ... on AppManagedComponents {
        locationName
        components {
          ...AppManagedComponentFragment
        }
      }
      ...PythonErrorFragment
    }
  }
  ${APP_MANAGED_COMPONENT_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const SET_APP_MANAGED_COMPONENT_MUTATION = gql`
  mutation SetAppManagedComponentMutation(
    $locationName: String!
    $componentId: String!
    $componentType: String!
    $attributes: String!
  ) {
    setAppManagedComponent(
      locationName: $locationName
      componentId: $componentId
      componentType: $componentType
      attributes: $attributes
    ) {
      ... on SetAppManagedComponentSuccess {
        component {
          ...AppManagedComponentFragment
        }
      }
      ... on UnauthorizedError {
        message
      }
      ...PythonErrorFragment
    }
  }
  ${APP_MANAGED_COMPONENT_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const DELETE_APP_MANAGED_COMPONENT_MUTATION = gql`
  mutation DeleteAppManagedComponentMutation($locationName: String!, $componentId: String!) {
    deleteAppManagedComponent(locationName: $locationName, componentId: $componentId) {
      ... on DeleteAppManagedComponentSuccess {
        locationName
        componentId
      }
      ... on UnauthorizedError {
        message
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
