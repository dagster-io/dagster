import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';

export const UI_COMPONENT_FRAGMENT = gql`
  fragment UIComponentFragment on UIComponent {
    componentId
    componentType
    attributes
  }
`;

export const CODE_LOCATION_UI_COMPONENTS_QUERY = gql`
  query CodeLocationUIComponentsQuery($locationName: String!) {
    uiComponentsForLocationOrError(locationName: $locationName) {
      ... on UIComponents {
        locationName
        components {
          ...UIComponentFragment
        }
      }
      ...PythonErrorFragment
    }
  }
  ${UI_COMPONENT_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const SET_UI_COMPONENT_MUTATION = gql`
  mutation SetUIComponentMutation(
    $locationName: String!
    $componentId: String!
    $componentType: String!
    $attributes: String!
  ) {
    setUIComponent(
      locationName: $locationName
      componentId: $componentId
      componentType: $componentType
      attributes: $attributes
    ) {
      ... on SetUIComponentSuccess {
        component {
          ...UIComponentFragment
        }
      }
      ... on UnauthorizedError {
        message
      }
      ...PythonErrorFragment
    }
  }
  ${UI_COMPONENT_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const DELETE_UI_COMPONENT_MUTATION = gql`
  mutation DeleteUIComponentMutation($locationName: String!, $componentId: String!) {
    deleteUIComponent(locationName: $locationName, componentId: $componentId) {
      ... on DeleteUIComponentSuccess {
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
