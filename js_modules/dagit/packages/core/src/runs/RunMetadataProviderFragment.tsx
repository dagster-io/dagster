import {gql} from '@apollo/client';

import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntry';

export const RUN_METADATA_PROVIDER_MESSAGE_FRAGMENT = gql`
  fragment RunMetadataProviderMessageFragment on DagsterRunEvent {
    __typename
    ... on MessageEvent {
      message
      timestamp
      stepKey
    }
    ... on MarkerEvent {
      markerStart
      markerEnd
    }
    ... on ObjectStoreOperationEvent {
      operationResult {
        op
        metadataEntries {
          ...MetadataEntryFragment
        }
      }
    }
    ... on LogsCapturedEvent {
      logKey
      stepKeys
      pid
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
`;
