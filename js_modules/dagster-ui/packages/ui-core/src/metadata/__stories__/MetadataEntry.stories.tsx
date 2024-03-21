import {Box, Checkbox} from '@dagster-io/ui-components';
import {useState} from 'react';

import {assertUnreachable} from '../../app/Util';
import {
  BoolMetadataEntry,
  IntMetadataEntry,
  JsonMetadataEntry,
  TableSchemaMetadataEntry,
} from '../../graphql/types';
import {MetadataEntries} from '../MetadataEntry';
import {MetadataEntryFragment} from '../types/MetadataEntry.types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'MetadataEntries',
  component: MetadataEntries,
};

const MetadataEntryTypes: MetadataEntryFragment['__typename'][] = [
  'PathMetadataEntry',
  'JsonMetadataEntry',
  'UrlMetadataEntry',
  'TextMetadataEntry',
  'MarkdownMetadataEntry',
  'PythonArtifactMetadataEntry',
  'FloatMetadataEntry',
  'IntMetadataEntry',
  'BoolMetadataEntry',
  'NullMetadataEntry',
  'PipelineRunMetadataEntry',
  'AssetMetadataEntry',
  'JobMetadataEntry',
  'TableColumnLineageMetadataEntry',
  'TableMetadataEntry',
  'TableSchemaMetadataEntry',
  'NotebookMetadataEntry',
  'TimestampMetadataEntry',
];

const MetadataTableSchema: TableSchemaMetadataEntry['schema'] = {
  __typename: 'TableSchema',
  constraints: {
    __typename: 'TableConstraints',
    other: [],
  },
  columns: [
    {
      __typename: 'TableColumn',
      name: 'id',
      type: 'int4',
      description: 'Id',
      constraints: {
        __typename: 'TableColumnConstraints',
        nullable: false,
        unique: true,
        other: [],
      },
    },
    {
      __typename: 'TableColumn',
      name: 'first_name',
      type: 'First Name',
      description: null,
      constraints: {
        __typename: 'TableColumnConstraints',
        nullable: false,
        unique: false,
        other: [],
      },
    },
    {
      __typename: 'TableColumn',
      name: 'last_name',
      type: 'Last Name',
      description: null,
      constraints: {
        __typename: 'TableColumnConstraints',
        nullable: false,
        unique: false,
        other: [],
      },
    },
  ],
};

function buildMockMetadataEntry(type: MetadataEntryFragment['__typename']): MetadataEntryFragment {
  switch (type) {
    case 'PathMetadataEntry':
      return {
        __typename: 'PathMetadataEntry',
        description: 'This is the description',
        label: 'my_path',
        path: '/dagster-homee/this/asset/path',
      };
    case 'JsonMetadataEntry':
      return {
        __typename: 'JsonMetadataEntry',
        description: 'This is the description',
        label: 'my_json',
        jsonString: JSON.stringify({
          short_value: 12,
          depth: 1235123.2315123,
          a: 'http://localhost:3000/assets/yoyo_singledim_staticla?partition=GA',
          b: 'http://localhost:3000/assets/yoyo_singledim_staticla?partition=GA',
          c: 'http://localhost:3000/assets/yoyo_singledim_staticla?partition=GA',
          d: 'http://localhost:3000/assets/yoyo_singledim_staticla?partition=GA',
          e: 'http://localhost:3000/assets/yoyo_singledim_staticla?partition=GA',
          f: 'http://localhost:3000/assets/yoyo_singledim_staticla?partition=GA',
          g: 'http://localhost:3000/assets/yoyo_singledim_staticla?partition=GA',
          h: 'http://localhost:3000/assets/yoyo_singledim_staticla?partition=GA',
          i: 'http://localhost:3000/assets/yoyo_singledim_staticla?partition=GA',
          version: 'ff639e01c58132962daa912789317898f710ee9a491123f58f23569e0706570b',
          other: 'ff639e01c58132962daa912789317898f710ee9a491123f58f23569e0706570b',
          longer_value: 'hello_world',
          another: {object: 'here', this_is_another: 'key_to_make_this_long'},
          tags: [
            {
              key: 'external-system/code_version',
              value: '1369974d-cfab-4e03-82a6-d9430b847814',
            },
            {
              key: 'external-system/logical_version',
              value: '5133d9b282809abd0d1ae6ab5c1b6175af7cc4d91d7543bfa7141aef71fba39e',
            },
          ],
        }),
      };

    case 'UrlMetadataEntry':
      return {
        __typename: 'UrlMetadataEntry',
        description: 'This is the description',
        label: 'my_url',
        url: 'http://localhost:3000/assets/yoyo_singledim_staticla?partition=GA',
      };
    case 'TextMetadataEntry':
      return {
        __typename: 'TextMetadataEntry',
        description: 'This is the description',
        label: 'my_text',
        text: 'hello world',
      };
    case 'MarkdownMetadataEntry':
      return {
        __typename: 'MarkdownMetadataEntry',
        description: 'This is the description',
        label: 'my_markdown',
        mdStr: '## Hello World\n\nCurious if [Visit Apple.com](https://apple.com/) really works.',
      };
    case 'PythonArtifactMetadataEntry':
      return {
        __typename: 'PythonArtifactMetadataEntry',
        label: 'my_artifact',
        name: 'artifact_name',
        module: 'test.py',
        description: 'This is my artifact descripton',
      };
    case 'FloatMetadataEntry':
      return {
        __typename: 'FloatMetadataEntry',
        description: 'This is the description',
        label: 'my_float',
        floatValue: 1234.12,
      };
    case 'IntMetadataEntry':
      return {
        __typename: 'IntMetadataEntry',
        description: 'This is the description',
        label: 'my_int',
        intValue: 12,
        intRepr: '12',
      };
    case 'BoolMetadataEntry':
      return {
        __typename: 'BoolMetadataEntry',
        description: 'This is the description',
        label: 'my_bool',
        boolValue: true,
      };
    case 'NullMetadataEntry':
      return {
        __typename: 'NullMetadataEntry',
        description: 'This is the description',
        label: 'always_null',
      };
    case 'PipelineRunMetadataEntry':
      return {
        __typename: 'PipelineRunMetadataEntry',
        description: 'This is the description',
        label: 'my_run',
        runId: '2a85aae4-b31f-44db-bd1c-6161549e4a3e',
      };
    case 'AssetMetadataEntry':
      return {
        __typename: 'AssetMetadataEntry',
        description: 'This is the description',
        label: 'my_asset',
        assetKey: {__typename: 'AssetKey', path: ['asset_1']},
      };
    case 'JobMetadataEntry':
      return {
        __typename: 'JobMetadataEntry',
        description: 'This is the description',
        label: 'my_job',
        jobName: 'my_job',
        locationName: 'my_location_name',
        repositoryName: null,
      };
    case 'TableColumnLineageMetadataEntry':
      return {
        __typename: 'TableColumnLineageMetadataEntry',
        description: 'This is the description',
        label: 'my_table_column_lineage',
        lineage: [
          {
            __typename: 'TableColumnLineageEntry',
            columnName: 'column_a',
            columnDeps: [
              {
                __typename: 'TableColumnDep',
                assetKey: {path: ['asset_1'], __typename: 'AssetKey'},
                columnName: 'column_a',
              },
            ],
          },
        ],
      };
    case 'TableMetadataEntry':
      return {
        __typename: 'TableMetadataEntry',
        description: 'This is the description',
        label: 'my_table',
        table: {
          __typename: 'Table',
          schema: MetadataTableSchema,
          records: ['1\tBen\tGotow', '2\tOther\tUser', '3\tFirst\tLast'],
        },
      };
    case 'TableSchemaMetadataEntry':
      return {
        __typename: 'TableSchemaMetadataEntry',
        description: 'This is the description',
        label: 'my_table_schema',
        schema: MetadataTableSchema,
      };
    case 'NotebookMetadataEntry':
      return {
        __typename: 'NotebookMetadataEntry',
        description: 'This is the description',
        label: 'my_path',
        path: '/this/is/a/notebook-path',
      };
    case 'TimestampMetadataEntry':
      return {
        __typename: 'TimestampMetadataEntry',
        description: 'This is the description',
        label: 'my_timestamp',
        timestamp: 1710187280.5,
      };
    default:
      return assertUnreachable(type);
  }
}

const MetadataEntryMocks = [
  // Ensure we have at least one mock for every metadata entry type
  // using an exhaustive switch statement
  ...MetadataEntryTypes.map(buildMockMetadataEntry),

  // Explicitly add more test cases that are interesting
  {
    __typename: 'BoolMetadataEntry',
    description: 'This is the description',
    label: 'my_null_bool',
    boolValue: null, // Null value
  } as BoolMetadataEntry,

  {
    __typename: 'IntMetadataEntry',
    description: 'This is the description',
    label: 'my_huge_int',
    intValue: null,
    intRepr: '21474836472147483147483147483647', // Cannot be expressed in JS
  } as IntMetadataEntry,

  {
    __typename: 'JsonMetadataEntry',
    description: 'This is the description',
    label: 'my_short_json',
    jsonString: '{"short_value": 12}', // Very short JSON is inlined
  } as JsonMetadataEntry,

  {
    __typename: 'TableSchemaMetadataEntry',
    description: 'This is the description',
    label: 'my_table_schema',
    schema: {
      ...MetadataTableSchema,
      columns: [
        ...MetadataTableSchema.columns,
        ...MetadataTableSchema.columns,
        ...MetadataTableSchema.columns,
        ...MetadataTableSchema.columns,
        ...MetadataTableSchema.columns,
      ],
    },
  } as TableSchemaMetadataEntry,
];

export const EmptyState = () => {
  const [expandSmallValues, setExpandSmallValues] = useState(false);
  return (
    <Box style={{width: '950px', display: 'flex', flexDirection: 'column', gap: 12}}>
      <Checkbox
        label="Expand small values"
        checked={expandSmallValues}
        onChange={() => setExpandSmallValues(!expandSmallValues)}
      />
      <MetadataEntries entries={MetadataEntryMocks} expandSmallValues={expandSmallValues} />
    </Box>
  );
};
