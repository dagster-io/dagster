import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';

export const CODE_LOCATION_COMPONENT_TYPES_QUERY = gql`
  query CodeLocationComponentTypesQuery($locationName: String!) {
    componentTypesForLocationOrError(locationName: $locationName) {
      ... on ComponentTypes {
        locationName
        componentTypes {
          name
          namespace
          example
          schema
          formSchema {
            dataSchema
            uiSchema
          }
          description
          owners
          tags
          isUiEditable
        }
      }
      ... on RepositoryLocationNotFound {
        message
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
