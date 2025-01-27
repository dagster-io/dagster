import {
  Box,
  Button,
  CaptionMono,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  FontFamily,
  Group,
  Icon,
  Table,
  Tooltip,
  tryPrettyPrintJSON,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {TableSchema} from './TableSchema';
import {
  MetadataEntryFragment,
  TableMetadataEntryFragment,
} from './types/MetadataEntryFragment.types';
import {copyValue} from '../app/DomUtils';
import {assertUnreachable} from '../app/Util';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {CodeLink, getCodeReferenceKey} from '../code-links/CodeLink';
import {IntMetadataEntry, MaterializationEvent} from '../graphql/types';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {Markdown} from '../ui/Markdown';
import {NotebookButton} from '../ui/NotebookButton';
import {DUNDER_REPO_NAME, buildRepoAddress} from '../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../workspace/workspacePath';

const TIME_FORMAT = {showSeconds: true, showTimezone: true};

export const HIDDEN_METADATA_ENTRY_LABELS = new Set([
  'dagster_dbt/select',
  'dagster_dbt/exclude',
  'dagster-dbt/select',
  'dagster-dbt/exclude',
  'dagster_dbt/manifest',
  'dagster_dbt/dagster_dbt_translator',
  'dagster_embedded_elt/dagster_sling_translator',
  'dagster_embedded_elt/sling_replication_config',
]);

export type MetadataEntryLabelOnly = Pick<
  MaterializationEvent['metadataEntries'][0],
  '__typename' | 'label'
>;

export const isCanonicalRowCountMetadataEntry = (
  m: MetadataEntryLabelOnly,
): m is IntMetadataEntry =>
  m && m.__typename === 'IntMetadataEntry' && m.label === 'dagster/row_count';

export const LogRowStructuredContentTable = ({
  rows,
  styles,
}: {
  rows: {label: string; item: JSX.Element}[];
  styles?: React.CSSProperties;
}) => (
  <div style={{overflow: 'auto', paddingBottom: 10, ...(styles || {})}}>
    <StructuredContentTable cellPadding="0" cellSpacing="0">
      <tbody>
        {rows.map(({label, item}, idx) => (
          <tr key={idx} style={{display: 'flex'}}>
            <td
              style={{
                flex: 1,
                maxWidth: 'max-content',
              }}
            >
              {label}
            </td>
            <td style={{flex: 1}}>{item}</td>
          </tr>
        ))}
      </tbody>
    </StructuredContentTable>
  </div>
);

export const MetadataEntries = ({
  entries,
  expandSmallValues,
}: {
  entries?: MetadataEntryFragment[];
  expandSmallValues?: boolean;
}) => {
  if (!entries || !entries.length) {
    return null;
  }
  return (
    <LogRowStructuredContentTable
      rows={entries
        .filter((entry) => !HIDDEN_METADATA_ENTRY_LABELS.has(entry.label))
        .map((entry) => ({
          label: entry.label,
          item: <MetadataEntry entry={entry} expandSmallValues={expandSmallValues} />,
        }))}
    />
  );
};

export const MetadataEntry = ({
  entry,
  expandSmallValues,
  repoLocation,
}: {
  entry: MetadataEntryFragment;
  expandSmallValues?: boolean;
  repoLocation?: string;
}) => {
  switch (entry.__typename) {
    case 'PathMetadataEntry':
      return (
        <Group direction="row" spacing={8} alignItems="center">
          <MetadataEntryAction title="Copy to clipboard" onClick={(e) => copyValue(e, entry.path)}>
            {entry.path}
          </MetadataEntryAction>
          <IconButton onClick={(e) => copyValue(e, entry.path)}>
            <Icon name="copy_to_clipboard" color={Colors.accentGray()} />
          </IconButton>
        </Group>
      );

    case 'JsonMetadataEntry':
    case 'TableColumnLineageMetadataEntry':
      const jsonString =
        entry.__typename === 'JsonMetadataEntry' ? entry.jsonString : JSON.stringify(entry.lineage);
      return expandSmallValues && jsonString.length < 1000 ? (
        <div style={{whiteSpace: 'pre-wrap'}}>{tryPrettyPrintJSON(jsonString)}</div>
      ) : (
        <MetadataEntryDialogAction
          label={entry.label}
          copyContent={() => jsonString}
          content={() => (
            <Box
              background={Colors.backgroundLight()}
              margin={{bottom: 12}}
              padding={24}
              border="bottom"
              style={{whiteSpace: 'pre-wrap', fontFamily: FontFamily.monospace, overflow: 'auto'}}
            >
              {tryPrettyPrintJSON(jsonString)}
            </Box>
          )}
        >
          [Show JSON]
        </MetadataEntryDialogAction>
      );

    case 'UrlMetadataEntry':
      return (
        <Group direction="row" spacing={8} alignItems="center">
          <MetadataEntryAction href={entry.url} title="Open in a new tab" target="_blank">
            {entry.url}
          </MetadataEntryAction>
          <a href={entry.url} target="_blank" rel="noreferrer">
            <Icon name="link" color={Colors.accentGray()} />
          </a>
        </Group>
      );
    case 'TextMetadataEntry':
      return <>{entry.text}</>;
    case 'MarkdownMetadataEntry':
      return expandSmallValues && entry.mdStr.length < 1000 ? (
        <Markdown>{entry.mdStr}</Markdown>
      ) : (
        <MetadataEntryDialogAction
          label={entry.label}
          copyContent={() => entry.mdStr}
          content={() => (
            <Box
              padding={{vertical: 16, horizontal: 20}}
              background={Colors.backgroundDefault()}
              style={{overflow: 'auto'}}
              margin={{bottom: 12}}
            >
              <Markdown>{entry.mdStr}</Markdown>
            </Box>
          )}
        >
          [Show Markdown]
        </MetadataEntryDialogAction>
      );
    case 'PythonArtifactMetadataEntry':
      return (
        <PythonArtifactLink
          name={entry.name}
          module={entry.module}
          description={entry.description || ''}
        />
      );
    case 'FloatMetadataEntry':
      return <>{entry.floatValue}</>;
    case 'TimestampMetadataEntry':
      return <TimestampDisplay timestamp={entry.timestamp} timeFormat={TIME_FORMAT} />;
    case 'IntMetadataEntry':
      return <>{entry.intValue !== null ? entry.intValue : entry.intRepr}</>;
    case 'BoolMetadataEntry':
      return <>{entry.boolValue !== null ? entry.boolValue.toString() : 'null'}</>;
    case 'NullMetadataEntry':
      return <>null</>;
    case 'PipelineRunMetadataEntry':
      return <MetadataEntryLink to={`/runs/${entry.runId}`}>{entry.runId}</MetadataEntryLink>;
    case 'AssetMetadataEntry':
      return (
        <MetadataEntryLink to={assetDetailsPathForKey(entry.assetKey)}>
          {displayNameForAssetKey(entry.assetKey)}
        </MetadataEntryLink>
      );
    case 'JobMetadataEntry':
      const repositoryName = entry.repositoryName || DUNDER_REPO_NAME;
      const workspacePath = workspacePathFromAddress(
        buildRepoAddress(repositoryName, entry.locationName),
        `/jobs/${entry.jobName}`,
      );
      return (
        <Box
          flex={{
            direction: 'row',
            gap: 8,
          }}
          style={{maxWidth: '100%'}}
        >
          <Icon name="job" color={Colors.accentGray()} />
          <MetadataEntryLink to={workspacePath}>{entry.jobName}</MetadataEntryLink>
        </Box>
      );
    case 'TableMetadataEntry':
      return <TableMetadataEntryComponent entry={entry} />;

    case 'TableSchemaMetadataEntry':
      return expandSmallValues && entry.schema.columns.length < 5 ? (
        <TableSchema schema={entry.schema} />
      ) : (
        <MetadataEntryDialogAction
          label={entry.label}
          modalWidth={900}
          copyContent={() => JSON.stringify(entry.schema, null, 2)}
          content={() => (
            <Box
              padding={{vertical: 16, horizontal: 20}}
              background={Colors.backgroundDefault()}
              style={{overflow: 'auto'}}
              margin={{bottom: 12}}
            >
              <TableSchema schema={entry.schema} />
            </Box>
          )}
        >
          [Show Table Schema]
        </MetadataEntryDialogAction>
      );
    case 'NotebookMetadataEntry':
      if (repoLocation) {
        return <NotebookButton path={entry.path} repoLocation={repoLocation} />;
      }
      return (
        <Group direction="row" spacing={8} alignItems="center">
          <MetadataEntryAction title="Copy to clipboard" onClick={(e) => copyValue(e, entry.path)}>
            {entry.path}
          </MetadataEntryAction>
          <IconButton onClick={(e) => copyValue(e, entry.path)}>
            <Icon name="copy_to_clipboard" color={Colors.accentGray()} />
          </IconButton>
        </Group>
      );
    case 'CodeReferencesMetadataEntry':
      return (
        <MetadataEntryDialogAction
          label={entry.label}
          modalWidth={900}
          content={() => (
            <Box
              padding={{vertical: 16, horizontal: 20}}
              background={Colors.backgroundDefault()}
              margin={{bottom: 12}}
              flex={{direction: 'column', gap: 8, alignItems: 'stretch'}}
            >
              {entry.codeReferences &&
                entry.codeReferences.map((ref) => (
                  <CodeLink key={getCodeReferenceKey(ref)} sourceLocation={ref} />
                ))}
            </Box>
          )}
        >
          [Show Code References]
        </MetadataEntryDialogAction>
      );
    default:
      return assertUnreachable(entry);
  }
};

const IconButton = styled.button`
  background: transparent;
  border: 0;
  cursor: pointer;
  display: block;
  padding: 0;
`;

const PythonArtifactLink = ({
  name,
  module,
  description,
}: {
  name: string;
  module: string;
  description: string;
}) => (
  <>
    <Tooltip
      hoverOpenDelay={100}
      position="top"
      content={`${module}.${name}`}
      usePortal
      modifiers={{
        preventOverflow: {enabled: false},
        flip: {enabled: false},
      }}
    >
      <span style={{cursor: 'pointer', textDecoration: 'underline'}}>{name}</span>
    </Tooltip>{' '}
    - {description}
  </>
);

const MetadataEntryDialogAction = (props: {
  children: React.ReactNode;
  label: string;
  modalWidth?: number;
  content: () => React.ReactNode;
  copyContent?: () => string;
}) => {
  const [open, setOpen] = React.useState(false);
  return (
    <>
      <MetadataEntryAction onClick={() => setOpen(true)}>{props.children}</MetadataEntryAction>
      <Dialog
        icon="info"
        style={{width: props.modalWidth || 'auto', minWidth: 400, maxWidth: '80vw'}}
        title={props.label}
        onClose={() => setOpen(false)}
        isOpen={open}
      >
        {props.content()}
        <DialogFooter>
          {props.copyContent && (
            <Button
              onClick={(e: React.MouseEvent) =>
                props.copyContent && copyValue(e, props.copyContent())
              }
            >
              Copy
            </Button>
          )}
          <Button intent="primary" autoFocus={true} onClick={() => setOpen(false)}>
            Close
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );
};

export const TableMetadataEntryComponent = ({entry}: {entry: TableMetadataEntryFragment}) => {
  const [showSchema, setShowSchema] = React.useState(false);

  const schema = entry.table.schema;
  const invalidRecords: string[] = [];

  const records = entry.table.records
    .map((record) => {
      try {
        return JSON.parse(record);
      } catch {
        invalidRecords.push(record);
        return null;
      }
    })
    .filter((record): record is Record<string, any> => record !== null);

  return (
    <Box flex={{direction: 'column', gap: 8}}>
      <MetadataEntryAction onClick={() => setShowSchema(true)}>Show schema</MetadataEntryAction>
      <Table style={{borderRight: `1px solid ${Colors.keylineDefault()}`}} $compact>
        <thead>
          <tr>
            {schema.columns.map((column) => (
              <th key={column.name}>{column.name}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {records.map((record, idx) => (
            <tr key={idx}>
              {schema.columns.map((column) => (
                <td key={column.name}>{record[column.name]?.toString()}</td>
              ))}
            </tr>
          ))}
          {invalidRecords.map((record, ii) => (
            <tr key={`invalid-${ii}`}>
              <td colSpan={schema.columns.length}>
                <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                  <Icon name="warning" />
                  <div>Could not parse record:</div>
                </Box>
                <div>
                  <Tooltip
                    content={<div style={{maxWidth: '400px'}}>{record}</div>}
                    placement="top"
                  >
                    <CaptionMono>
                      {record.length > 20 ? `${record.slice(0, 20)}…` : record}
                    </CaptionMono>
                  </Tooltip>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
      <Dialog isOpen={showSchema} title={`Schema for ${entry.label}`}>
        <DialogBody>
          <TableSchema schema={schema} />
        </DialogBody>
        <DialogFooter topBorder>
          <Button
            intent="primary"
            autoFocus={true}
            onClick={() => {
              setShowSchema(false);
            }}
          >
            Close
          </Button>
        </DialogFooter>
      </Dialog>
    </Box>
  );
};

const MetadataEntryAction = styled.a`
  text-decoration: underline;
  color: inherit;
  &:hover {
    color: inherit;
  }
`;

export const MetadataEntryLink = styled(Link)`
  text-decoration: underline;
  color: inherit;
  &:hover {
    color: inherit;
  }
`;

export const StructuredContentTable = styled.table`
  width: 100%;
  padding: 0;
  margin-top: 4px;
  border-top: 1px solid ${Colors.keylineDefault()};
  border-left: 1px solid ${Colors.keylineDefault()};
  background: ${Colors.backgroundLighter()};

  td:first-child {
    color: ${Colors.textLight()};
  }

  &&& tbody > tr > td {
    padding: 4px 8px;
    border-bottom: 1px solid ${Colors.keylineDefault()};
    border-right: 1px solid ${Colors.keylineDefault()};
    vertical-align: top;
    box-shadow: none !important;
  }
`;
