import React, {useMemo, useRef, useState} from 'react';

import {
  AssetColumnLineageQuery,
  AssetColumnLineageQueryVariables,
} from './types/useColumnLineageDataForAssets.types';
import {gql, useApolloClient} from '../../apollo-client';
import {toGraphId} from '../../asset-graph/Utils';
import {AssetKeyInput, DefinitionTag, TableColumnLineageMetadataEntry} from '../../graphql/types';
import {isCanonicalColumnLineageEntry} from '../../metadata/TableSchema';
import {useBlockTraceUntilTrue} from '../../performance/TraceContext';
import {buildConsolidatedColumnSchema} from '../buildConsolidatedColumnSchema';

export type AssetColumnLineageLocalColumn = {
  name: string;
  type: string | null;
  description: string | null;
  tags: DefinitionTag[];
  asOf: string | undefined; // materialization timestamp
  upstream: {
    assetKey: AssetKeyInput;
    columnName: string;
  }[];
};

export type AssetColumnLineageLocal = {
  columns: {
    [column: string]: AssetColumnLineageLocalColumn;
  };
  hasLineage: boolean;
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

  const definitionLineageMetadata = asset.metadataEntries.find(isCanonicalColumnLineageEntry);
  const materializationLineageMetadata = materialization?.metadataEntries.find(
    isCanonicalColumnLineageEntry,
  );
  const lineageMetadata: TableColumnLineageMetadataEntry | undefined =
    materializationLineageMetadata || definitionLineageMetadata;

  const {tableSchema} = buildConsolidatedColumnSchema({
    materialization,
    definition: asset,
    definitionLoadTimestamp: undefined,
  });

  const schemaParsed = tableSchema?.schema
    ? Object.fromEntries(tableSchema.schema.columns.map((col) => [col.name, col]))
    : {};

  const lineageByName = lineageMetadata?.lineage
    ? Object.fromEntries(lineageMetadata.lineage.map((l) => [l.columnName, l]))
    : {};

  const columnNames: string[] = !!lineageMetadata
    ? Object.keys(lineageByName)
    : Object.keys(schemaParsed);

  return {
    hasLineage: !!lineageMetadata,
    columns: Object.fromEntries(
      columnNames.map((columnName) => [
        columnName,
        {
          name: columnName,
          asOf: materialization?.timestamp,
          type: schemaParsed[columnName]?.type || null,
          description: schemaParsed[columnName]?.description || null,
          upstream: lineageByName[columnName]?.columnDeps || [],
          tags: schemaParsed[columnName]?.tags || [],
        },
      ]),
    ),
  };
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

  useBlockTraceUntilTrue(
    'useColumnLineageDataForAssets',
    Object.keys(loaded).length === assetKeys.length,
  );

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
              tags {
                key
                value
              }
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
                tags {
                  key
                  value
                }
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
