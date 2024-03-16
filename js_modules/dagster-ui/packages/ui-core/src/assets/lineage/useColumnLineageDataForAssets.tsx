import {gql, useApolloClient} from '@apollo/client';
import React, {useRef, useState} from 'react';

import {
  AssetColumnLineageQuery,
  AssetColumnLineageQueryVariables,
} from './types/useColumnLineageDataForAssets.types';
import {toGraphId} from '../../asset-graph/Utils';
import {AssetKeyInput} from '../../graphql/types';
import {isCanonicalColumnLineageEntry} from '../../metadata/TableSchema';
import {buildConsolidatedColumnSchema} from '../buildConsolidatedColumnSchema';

export type AssetColumnLineageServer = {
  [column: string]: {
    upstream_asset_key: string[][];
    upstream_column_name: string;
  }[];
};

export type AssetColumnLineageLocal = {
  [column: string]: {
    name: string;
    type: string | null;
    description: string | null;
    upstream: {
      assetKeys: AssetKeyInput[];
      columnName: string;
    }[];
  };
};

export type AssetColumnLineages = {[graphId: string]: AssetColumnLineageLocal | undefined};

const getColumnLineage = (
  asset: AssetColumnLineageQuery['assetNodes'][0],
): AssetColumnLineageLocal | undefined => {
  const materialization = asset.assetMaterializations[0];
  const lineageMetadata = materialization?.metadataEntries.find(isCanonicalColumnLineageEntry);
  if (!lineageMetadata) {
    return undefined;
  }

  const {tableSchema} = buildConsolidatedColumnSchema({
    materialization,
    definition: asset,
    definitionLoadTimestamp: undefined,
  });

  const lineageParsed: AssetColumnLineageServer = JSON.parse(lineageMetadata.jsonString);
  const schemaParsed = tableSchema?.schema
    ? Object.fromEntries(tableSchema.schema.columns.map((col) => [col.name, col]))
    : {};

  return Object.fromEntries(
    Object.entries(lineageParsed).map(([column, m]) => [
      column,
      {
        name: column,
        type: schemaParsed[column]?.type || null,
        description: schemaParsed[column]?.description || null,
        upstream: m.map((u) => ({
          assetKeys: u.upstream_asset_key.map((path) => ({path})),
          columnName: u.upstream_column_name,
        })),
      },
    ]),
  );
};

export function useColumnLineageDataForAssets(assetKeys: AssetKeyInput[]) {
  const [loaded, setLoaded] = useState<AssetColumnLineages>({});
  const missing = assetKeys.filter((a) => !loaded[toGraphId(a)]);
  const missingJSON = JSON.stringify(missing);
  const client = useApolloClient();
  const fetching = useRef(false);

  React.useEffect(() => {
    const missingAssetKeys = JSON.parse(missingJSON);
    const fetch = async () => {
      fetching.current = true;
      const {data} = await client.query<AssetColumnLineageQuery, AssetColumnLineageQueryVariables>({
        query: ASSET_COLUMN_LINEAGE_QUERY,
        variables: {assetKeys: missingAssetKeys},
      });
      fetching.current = false;

      setLoaded((loaded) => ({
        ...loaded,
        ...Object.fromEntries(
          data.assetNodes.map((n) => [toGraphId(n.assetKey), getColumnLineage(n)]),
        ),
      }));
    };
    if (!fetching.current && missingAssetKeys.length) {
      void fetch();
    }
  }, [client, missingJSON]);

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
          ... on JsonMetadataEntry {
            jsonString
          }
        }
      }
    }
  }
`;
