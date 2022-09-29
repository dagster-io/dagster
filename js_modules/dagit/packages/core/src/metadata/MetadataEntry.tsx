import {gql} from '@apollo/client';
import {
  Box,
  Button,
  Colors,
  DialogFooter,
  Dialog,
  Group,
  Icon,
  Markdown,
  Tooltip,
  FontFamily,
  tryPrettyPrintJSON,
} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {copyValue} from '../app/DomUtils';
import {TABLE_SCHEMA_FRAGMENT} from '../app/TableSchemaFragment';
import {assertUnreachable} from '../app/Util';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';

import {TableSchema} from './TableSchema';
import {MetadataEntryFragment} from './types/MetadataEntryFragment';

export interface IMetadataEntries {
  metadataEntries: MetadataEntryFragment[];
}

export const LogRowStructuredContentTable: React.FC<{
  rows: {label: string; item: JSX.Element}[];
  styles?: React.CSSProperties;
}> = ({rows, styles}) => (
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

export const MetadataEntries: React.FC<{
  entries?: MetadataEntryFragment[];
}> = ({entries}) => {
  if (!entries || !entries.length) {
    return null;
  }
  return (
    <LogRowStructuredContentTable
      rows={entries.map((entry) => ({
        label: entry.label,
        item: <MetadataEntry entry={entry} />,
      }))}
    />
  );
};

export const MetadataEntry: React.FC<{
  entry: MetadataEntryFragment;
  expandSmallValues?: boolean;
}> = ({entry, expandSmallValues}) => {
  switch (entry.__typename) {
    case 'PathMetadataEntry':
      return (
        <Group direction="row" spacing={8} alignItems="center">
          <MetadataEntryAction title="Copy to clipboard" onClick={(e) => copyValue(e, entry.path)}>
            {entry.path}
          </MetadataEntryAction>
          <IconButton onClick={(e) => copyValue(e, entry.path)}>
            <Icon name="assignment" color={Colors.Gray500} />
          </IconButton>
        </Group>
      );

    case 'JsonMetadataEntry':
      return expandSmallValues && entry.jsonString.length < 1000 ? (
        <div style={{whiteSpace: 'pre-wrap'}}>{tryPrettyPrintJSON(entry.jsonString)}</div>
      ) : (
        <MetadataEntryModalAction
          label={entry.label}
          copyContent={() => entry.jsonString}
          content={() => (
            <Box
              background={Colors.Gray100}
              margin={{bottom: 12}}
              padding={24}
              border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
              style={{whiteSpace: 'pre-wrap', fontFamily: FontFamily.monospace, overflow: 'auto'}}
            >
              {tryPrettyPrintJSON(entry.jsonString)}
            </Box>
          )}
        >
          [Show JSON]
        </MetadataEntryModalAction>
      );

    case 'UrlMetadataEntry':
      return (
        <Group direction="row" spacing={8} alignItems="center">
          <MetadataEntryAction href={entry.url} title="Open in a new tab" target="_blank">
            {entry.url}
          </MetadataEntryAction>
          <a href={entry.url} target="_blank" rel="noreferrer">
            <Icon name="link" color={Colors.Gray500} />
          </a>
        </Group>
      );
    case 'TextMetadataEntry':
      return <>{entry.text}</>;
    case 'MarkdownMetadataEntry':
      return expandSmallValues && entry.mdStr.length < 1000 ? (
        <Markdown>{entry.mdStr}</Markdown>
      ) : (
        <MetadataEntryModalAction
          label={entry.label}
          copyContent={() => entry.mdStr}
          content={() => (
            <Box
              padding={{vertical: 16, horizontal: 20}}
              background={Colors.White}
              style={{overflow: 'auto'}}
              margin={{bottom: 12}}
            >
              <Markdown>{entry.mdStr}</Markdown>
            </Box>
          )}
        >
          [Show Markdown]
        </MetadataEntryModalAction>
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
    case 'IntMetadataEntry':
      return <>{entry.intValue !== null ? entry.intValue : entry.intRepr}</>;
    case 'BoolMetadataEntry':
      return entry.boolValue !== null ? <>{entry.boolValue.toString()}</> : null;
    case 'PipelineRunMetadataEntry':
      return (
        <MetadataEntryLink to={`/instance/runs/${entry.runId}`}>{entry.runId}</MetadataEntryLink>
      );
    case 'AssetMetadataEntry':
      return (
        <MetadataEntryLink to={assetDetailsPathForKey(entry.assetKey)}>
          {displayNameForAssetKey(entry.assetKey)}
        </MetadataEntryLink>
      );
    case 'TableMetadataEntry':
      return null;
    case 'TableSchemaMetadataEntry':
      return <TableSchema schema={entry.schema} />;
    default:
      return assertUnreachable(entry);
  }
};

export const METADATA_ENTRY_FRAGMENT = gql`
  fragment MetadataEntryFragment on MetadataEntry {
    __typename
    label
    description
    ... on PathMetadataEntry {
      path
    }
    ... on JsonMetadataEntry {
      jsonString
    }
    ... on UrlMetadataEntry {
      url
    }
    ... on TextMetadataEntry {
      text
    }
    ... on MarkdownMetadataEntry {
      mdStr
    }
    ... on PythonArtifactMetadataEntry {
      module
      name
    }
    ... on FloatMetadataEntry {
      floatValue
    }
    ... on IntMetadataEntry {
      intValue
      intRepr
    }
    ... on BoolMetadataEntry {
      boolValue
    }
    ... on PipelineRunMetadataEntry {
      runId
    }
    ... on AssetMetadataEntry {
      assetKey {
        path
      }
    }
    ... on TableMetadataEntry {
      table {
        records
        schema {
          ...TableSchemaFragment
        }
      }
    }
    ... on TableSchemaMetadataEntry {
      schema {
        ...TableSchemaFragment
      }
    }
  }
  ${TABLE_SCHEMA_FRAGMENT}
`;

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

const MetadataEntryModalAction: React.FC<{
  label: string;
  content: () => React.ReactNode;
  copyContent: () => string;
}> = (props) => {
  const [open, setOpen] = React.useState(false);
  return (
    <>
      <MetadataEntryAction onClick={() => setOpen(true)}>{props.children}</MetadataEntryAction>
      <Dialog
        icon="info"
        style={{width: 'auto', minWidth: 400, maxWidth: '80vw'}}
        title={props.label}
        onClose={() => setOpen(false)}
        isOpen={open}
      >
        {props.content()}
        <DialogFooter>
          <Button onClick={(e: React.MouseEvent) => copyValue(e, props.copyContent())}>Copy</Button>
          <Button intent="primary" autoFocus={true} onClick={() => setOpen(false)}>
            Close
          </Button>
        </DialogFooter>
      </Dialog>
    </>
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

const StructuredContentTable = styled.table`
  width: 100%;
  padding: 0;
  margin-top: 4px;
  border-top: 1px solid ${Colors.KeylineGray};
  border-left: 1px solid ${Colors.KeylineGray};
  background: ${Colors.Gray50};

  td:first-child {
    color: ${Colors.Gray400};
  }

  &&& tbody > tr > td {
    padding: 4px 8px;
    border-bottom: 1px solid ${Colors.KeylineGray};
    border-right: 1px solid ${Colors.KeylineGray};
    vertical-align: top;
    box-shadow: none !important;
  }
`;
