import {gql, useApolloClient} from '@apollo/client';
import React, {useMemo, useRef, useState} from 'react';

import {
  AssetColumnLineageQuery,
  AssetColumnLineageQueryVariables,
} from './types/useColumnLineageDataForAssets.types';
import {toGraphId} from '../../asset-graph/Utils';
import {AssetKeyInput} from '../../graphql/types';
import {isCanonicalColumnLineageEntry} from '../../metadata/TableSchema';
import {buildConsolidatedColumnSchema} from '../buildConsolidatedColumnSchema';

export type AssetColumnLineageLocalColumn = {
  name: string;
  type: string | null;
  description: string | null;
  asOf: string | undefined; // materialization timestamp
  upstream: {
    assetKey: AssetKeyInput;
    columnName: string;
  }[];
};

export type AssetColumnLineageLocal = {
  [column: string]: AssetColumnLineageLocalColumn;
};

export type AssetColumnLineages = {[graphId: string]: AssetColumnLineageLocal | undefined};

/**
 * The column definitions and the column lineage are in two separate metadata entries,
 * and the definitions may be specified in definition-time or materialization-time metadata.
 * Parse them both and combine the results into a single representation of asset columns
 * that is easier for the rest of the front-end to use.
 */
const getColumnLineage = (
  asset: AssetColumnLineageQuery['assetNodes'][0],
): AssetColumnLineageLocal => {
  const materialization = asset.assetMaterializations[0];
  const lineageMetadata = materialization?.metadataEntries.find(isCanonicalColumnLineageEntry);
  if (!lineageMetadata) {
    // Note: We return empty rather than undefined / null so the hook does not try to fetch
    // this again as if it were still missing
    return {};
  }

  const {tableSchema} = buildConsolidatedColumnSchema({
    materialization,
    definition: asset,
    definitionLoadTimestamp: undefined,
  });

  const schemaParsed = tableSchema?.schema
    ? Object.fromEntries(tableSchema.schema.columns.map((col) => [col.name, col]))
    : {};

  return Object.fromEntries(
    lineageMetadata.lineage.map(({columnName, columnDeps}) => [
      columnName,
      {
        name: columnName,
        asOf: materialization?.timestamp,
        type: schemaParsed[columnName]?.type || null,
        description: schemaParsed[columnName]?.description || null,
        upstream: columnDeps,
      },
    ]),
  );
};

export function useColumnLineageDataForAssets(assetKeys: AssetKeyInput[]) {
  const [loaded, setLoaded] = useState<AssetColumnLineages>({});
  const client = useApolloClient();
  const fetching = useRef(false);
  const missing = useMemo(
    () => assetKeys.filter((a) => !loaded[toGraphId(a)]),
    [assetKeys, loaded],
  );

  React.useEffect(() => {
    const fetch = async () => {
      fetching.current = true;
      const {data} = await client.query<AssetColumnLineageQuery, AssetColumnLineageQueryVariables>({
        query: ASSET_COLUMN_LINEAGE_QUERY,
        variables: {assetKeys: missing},
      });
      fetching.current = false;

      setLoaded((loaded) => ({
        ...loaded,
        ...Object.fromEntries(
          data.assetNodes.map((n) => [toGraphId(n.assetKey), getColumnLineage(n)]),
        ),
      }));
    };
    if (!fetching.current && missing.length) {
      void fetch();
    }
  }, [client, missing]);

  return loaded;
}

const ASSET_COLUMN_LINEAGE_QUERY = gql`
  query AssetColumnLineage($assetKeys: [AssetKeyInput!]!) {
    assetNodes(loadMaterializations: true, assetKeys: $assetKeys) {
      id
      assetKey {
        path
      }
      metadataEntries {
        __typename
        label
        ... on TableSchemaMetadataEntry {
          label
          schema {
            columns {
              name
              type
              description
            }
          }
        }
      }
      assetMaterializations(limit: 1) {
        timestamp
        metadataEntries {
          __typename
          label
          ... on TableSchemaMetadataEntry {
            label
            schema {
              columns {
                name
                type
                description
              }
            }
          }
          ... on TableColumnLineageMetadataEntry {
            lineage {
              columnName
              columnDeps {
                assetKey {
                  path
                }
                columnName
              }
            }
          }
        }
      }
    }
  }
`;
