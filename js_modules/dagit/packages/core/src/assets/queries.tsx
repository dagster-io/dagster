import {gql} from '@apollo/client';

import {METADATA_ENTRY_FRAGMENT} from '../runs/MetadataEntry';

export const ASSET_QUERY = gql`
  query AssetQuery($assetKey: AssetKeyInput!, $limit: Int!) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        key {
          path
        }
        assetMaterializations(limit: $limit) {
          partition
          runOrError {
            ... on PipelineRun {
              id
              runId
              mode
              status
              pipelineName
              pipelineSnapshotId
            }
          }
          materializationEvent {
            runId
            timestamp
            stepKey
            stepStats {
              endTime
              startTime
            }
            materialization {
              label
              description
              metadataEntries {
                ...MetadataEntryFragment
              }
            }
            assetLineage {
              assetKey {
                path
              }
              partitions
            }
          }
        }
      }
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
`;
