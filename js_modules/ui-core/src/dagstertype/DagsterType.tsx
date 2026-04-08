import {Box} from '@dagster-io/ui-components';
import {Spacing} from '@dagster-io/ui-components/src/components/types';

import {gql} from '../apollo-client';
import {DagsterTypeFragment} from './types/DagsterType.types';
import {gqlTypePredicate} from '../app/Util';
import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntryFragment';
import {TableSchema} from '../metadata/TableSchema';
import {MetadataEntryFragment} from '../metadata/types/MetadataEntryFragment.types';
import {Description} from '../pipelines/Description';
import {CONFIG_TYPE_SCHEMA_FRAGMENT} from '../typeexplorer/ConfigTypeSchema';
import styles from './css/DagsterType.module.css';

export const dagsterTypeKind = (type: {metadataEntries: MetadataEntryFragment[]}) => {
  const tableSchema = type.metadataEntries.find(gqlTypePredicate('TableSchemaMetadataEntry'));
  if (tableSchema) {
    return 'table';
  } else {
    return 'standard';
  }
};

const _DagsterTypeName = ({type, className}: {type: DagsterTypeFragment; className?: string}) => {
  const typeKind = dagsterTypeKind(type);
  const displayName = typeKind === 'standard' ? type.name : `${type.name} (${typeKind})`;
  return <Box className={className}>{displayName}</Box>;
};

export const DagsterTypeSummary = ({
  type,
  horizontalPadding,
}: {
  type: DagsterTypeFragment;
  horizontalPadding?: Spacing;
}) => {
  horizontalPadding = horizontalPadding || 0;
  const tableSchemaEntry = (type.metadataEntries || []).find(
    gqlTypePredicate('TableSchemaMetadataEntry'),
  );
  return (
    <Box
      flex={{direction: 'column', gap: 8}}
      padding={{horizontal: 24, vertical: 16}}
      style={{overflowY: 'auto'}}
    >
      {type.name && (
        <Box>
          <_DagsterTypeName className={styles.dagsterTypeName} type={type} />
        </Box>
      )}
      {type.description && (
        <Box padding={{horizontal: horizontalPadding}}>
          <Description description={type.description} />
        </Box>
      )}
      {tableSchemaEntry && (
        <Box border="top" style={{overflowY: 'auto', marginBottom: -12}} margin={{top: 4}}>
          <TableSchema schema={tableSchemaEntry.schema} itemHorizontalPadding={horizontalPadding} />
        </Box>
      )}
    </Box>
  );
};

// NOTE: Because you can't have a recursive fragment, inner types are limited.
export const DAGSTER_TYPE_FRAGMENT = gql`
  fragment DagsterTypeFragment on DagsterType {
    ...InnerDagsterTypeFragment
    innerTypes {
      ...InnerDagsterTypeFragment
    }
  }
  fragment InnerDagsterTypeFragment on DagsterType {
    __typename
    key
    name
    displayName
    description
    isNullable
    isList
    isBuiltin
    isNothing
    metadataEntries {
      ...MetadataEntryFragment
    }
    inputSchemaType {
      ...ConfigTypeSchemaFragment
      recursiveConfigTypes {
        ...ConfigTypeSchemaFragment
      }
    }
    outputSchemaType {
      ...ConfigTypeSchemaFragment
      recursiveConfigTypes {
        ...ConfigTypeSchemaFragment
      }
    }
  }

  ${METADATA_ENTRY_FRAGMENT}
  ${CONFIG_TYPE_SCHEMA_FRAGMENT}
`;
