import {gql} from '@apollo/client';
import {Button, Classes, Colors, Dialog, Icon, Position} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';
import ReactMarkdown from 'react-markdown';
import {Link} from 'react-router-dom';
import gfm from 'remark-gfm';
import styled from 'styled-components/macro';

import {copyValue} from '../app/DomUtils';
import {assertUnreachable} from '../app/Util';
import {Markdown} from '../ui/Markdown';

import {MetadataEntryFragment} from './types/MetadataEntryFragment';

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
    case 'EventPathMetadataEntry':
      return (
        <>
          <MetadataEntryAction
            title={'Copy to clipboard'}
            onClick={(e) => copyValue(e, entry.path)}
          >
            {entry.path}
          </MetadataEntryAction>{' '}
          <Icon
            icon="clipboard"
            iconSize={10}
            color={'#a88860'}
            style={{verticalAlign: 'initial'}}
            onClick={(e) => copyValue(e, entry.path)}
          />
        </>
      );

    case 'EventJsonMetadataEntry':
      return expandSmallValues && entry.jsonString.length < 1000 ? (
        <div style={{whiteSpace: 'pre-wrap'}}>
          {JSON.stringify(JSON.parse(entry.jsonString), null, 2)}
        </div>
      ) : (
        <MetadataEntryModalAction
          label={entry.label}
          copyContent={() => entry.jsonString}
          content={() => (
            <div style={{whiteSpace: 'pre-wrap'}}>
              {JSON.stringify(JSON.parse(entry.jsonString), null, 2)}
            </div>
          )}
        >
          [Show JSON]
        </MetadataEntryModalAction>
      );

    case 'EventUrlMetadataEntry':
      return (
        <>
          <MetadataEntryAction href={entry.url} title={`Open in a new tab`} target="__blank">
            {entry.url}
          </MetadataEntryAction>{' '}
          <a href={entry.url} target="__blank">
            <Icon icon="link" iconSize={10} color={'#a88860'} />
          </a>
        </>
      );
    case 'EventTextMetadataEntry':
      return <>{entry.text}</>;
    case 'EventMarkdownMetadataEntry':
      return expandSmallValues && entry.mdStr.length < 1000 ? (
        <Markdown>{entry.mdStr}</Markdown>
      ) : (
        <MetadataEntryModalAction
          label={entry.label}
          copyContent={() => entry.mdStr}
          content={() => <ReactMarkdown remarkPlugins={[gfm]}>{entry.mdStr}</ReactMarkdown>}
        >
          [Show Markdown]
        </MetadataEntryModalAction>
      );
    case 'EventPythonArtifactMetadataEntry':
      return (
        <PythonArtifactLink
          name={entry.name}
          module={entry.module}
          description={entry.description || ''}
        />
      );
    case 'EventFloatMetadataEntry':
      return <>{entry.floatValue}</>;
    case 'EventIntMetadataEntry':
      return <>{entry.intValue !== null ? entry.intValue : entry.intRepr}</>;
    case 'EventPipelineRunMetadataEntry':
      return (
        <MetadataEntryLink to={`/instance/runs/${entry.runId}`}>{entry.runId}</MetadataEntryLink>
      );
    case 'EventAssetMetadataEntry':
      return (
        <MetadataEntryLink
          to={`/instance/assets/${entry.assetKey.path.map(encodeURIComponent).join('/')}`}
        >
          {entry.assetKey.path.join(' > ')}
        </MetadataEntryLink>
      );
    default:
      return assertUnreachable(entry);
  }
};

export const METADATA_ENTRY_FRAGMENT = gql`
  fragment MetadataEntryFragment on EventMetadataEntry {
    __typename
    label
    description
    ... on EventPathMetadataEntry {
      path
    }
    ... on EventJsonMetadataEntry {
      jsonString
    }
    ... on EventUrlMetadataEntry {
      url
    }
    ... on EventTextMetadataEntry {
      text
    }
    ... on EventMarkdownMetadataEntry {
      mdStr
    }
    ... on EventPythonArtifactMetadataEntry {
      module
      name
    }
    ... on EventFloatMetadataEntry {
      floatValue
    }
    ... on EventIntMetadataEntry {
      intValue
      intRepr
    }
    ... on EventPipelineRunMetadataEntry {
      runId
    }
    ... on EventAssetMetadataEntry {
      assetKey {
        path
      }
    }
  }
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
      position={Position.TOP}
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

const MetadataEntryModalAction: React.FunctionComponent<{
  label: string;
  content: () => React.ReactNode;
  copyContent: () => string;
}> = (props) => {
  const [isExpanded, setExpanded] = React.useState(false);
  return (
    <>
      <MetadataEntryAction onClick={() => setExpanded(true)}>{props.children}</MetadataEntryAction>
      {isExpanded && (
        <Dialog
          icon="info-sign"
          usePortal={true}
          style={{width: 'auto', minWidth: 400, maxWidth: '80vw'}}
          title={props.label}
          onClose={() => setExpanded(false)}
          isOpen={true}
        >
          <MetadataEntryModalContent>{props.content()}</MetadataEntryModalContent>
          <div className={Classes.DIALOG_FOOTER}>
            <div className={Classes.DIALOG_FOOTER_ACTIONS}>
              <Button onClick={(e: React.MouseEvent) => copyValue(e, props.copyContent())}>
                Copy
              </Button>
              <Button intent="primary" autoFocus={true} onClick={() => setExpanded(false)}>
                Close
              </Button>
            </div>
          </div>
        </Dialog>
      )}
    </>
  );
};

const MetadataEntryModalContent = styled.div`
  font-size: 13px;
  overflow: auto;
  max-height: 500px;
  background: ${Colors.WHITE};
  border-top: 1px solid ${Colors.LIGHT_GRAY3};
  padding: 20px;
  margin: 0;
  margin-bottom: 20px;
`;

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
  border-top: 1px solid #dbc5ad;
  border-left: 1px solid #dbc5ad;
  background: #fffaf5;
  td:first-child {
    color: #a88860;
  }
  tbody > tr > td {
    padding: 4px;
    padding-right: 8px;
    border-bottom: 1px solid #dbc5ad;
    border-right: 1px solid #dbc5ad;
    vertical-align: top;
    box-shadow: none !important;
  }
`;
