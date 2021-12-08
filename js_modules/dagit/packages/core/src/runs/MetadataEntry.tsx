import {gql} from '@apollo/client';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {copyValue} from '../app/DomUtils';
import {assertUnreachable} from '../app/Util';
import {Box} from '../ui/Box';
import {ButtonWIP} from '../ui/Button';
import {ColorsWIP} from '../ui/Colors';
import {DialogBody, DialogFooter, DialogWIP} from '../ui/Dialog';
import {Group} from '../ui/Group';
import {IconWIP} from '../ui/Icon';
import {Markdown} from '../ui/Markdown';
import {Tooltip} from '../ui/Tooltip';
import {FontFamily} from '../ui/styles';
import {assetKeyToString} from '../workspace/asset-graph/Utils';

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
        <Group direction="row" spacing={8} alignItems="center">
          <MetadataEntryAction
            title={'Copy to clipboard'}
            onClick={(e) => copyValue(e, entry.path)}
          >
            {entry.path}
          </MetadataEntryAction>
          <IconButton onClick={(e) => copyValue(e, entry.path)}>
            <IconWIP name="assignment" color={ColorsWIP.Gray500} />
          </IconButton>
        </Group>
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
            <Box
              background={ColorsWIP.Gray100}
              margin={{bottom: 12}}
              padding={24}
              border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
              style={{whiteSpace: 'pre-wrap', fontFamily: FontFamily.monospace}}
            >
              {JSON.stringify(JSON.parse(entry.jsonString), null, 2)}
            </Box>
          )}
        >
          [Show JSON]
        </MetadataEntryModalAction>
      );

    case 'EventUrlMetadataEntry':
      return (
        <Group direction="row" spacing={8} alignItems="center">
          <MetadataEntryAction href={entry.url} title={`Open in a new tab`} target="_blank">
            {entry.url}
          </MetadataEntryAction>
          <a href={entry.url} target="_blank" rel="noreferrer">
            <IconWIP name="link" color={ColorsWIP.Gray500} />
          </a>
        </Group>
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
          content={() => (
            <DialogBody>
              <Markdown>{entry.mdStr}</Markdown>
            </DialogBody>
          )}
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
          {assetKeyToString(entry.assetKey)}
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

const MetadataEntryModalAction: React.FunctionComponent<{
  label: string;
  content: () => React.ReactNode;
  copyContent: () => string;
}> = (props) => {
  const [open, setOpen] = React.useState(false);
  return (
    <>
      <MetadataEntryAction onClick={() => setOpen(true)}>{props.children}</MetadataEntryAction>
      <DialogWIP
        icon="info"
        style={{width: 'auto', minWidth: 400, maxWidth: '80vw'}}
        title={props.label}
        onClose={() => setOpen(false)}
        isOpen={open}
      >
        {props.content()}
        <DialogFooter>
          <ButtonWIP onClick={(e: React.MouseEvent) => copyValue(e, props.copyContent())}>
            Copy
          </ButtonWIP>
          <ButtonWIP intent="primary" autoFocus={true} onClick={() => setOpen(false)}>
            Close
          </ButtonWIP>
        </DialogFooter>
      </DialogWIP>
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
  border-top: 1px solid ${ColorsWIP.KeylineGray};
  border-left: 1px solid ${ColorsWIP.KeylineGray};
  background: ${ColorsWIP.Gray50};

  td:first-child {
    color: ${ColorsWIP.Gray400};
  }

  &&& tbody > tr > td {
    padding: 4px 8px;
    border-bottom: 1px solid ${ColorsWIP.KeylineGray};
    border-right: 1px solid ${ColorsWIP.KeylineGray};
    vertical-align: top;
    box-shadow: none !important;
  }
`;
