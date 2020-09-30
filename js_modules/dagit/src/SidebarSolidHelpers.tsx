import {Code, Colors, Text} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {SectionHeader} from 'src/SidebarComponents';
import {titleOfIO} from 'src/Util';
import {SolidColumn} from 'src/runs/LogsRowComponents';

export type SolidLinkInfo = {
  solid: {name: string};
  definition: {name: string};
};

export interface SidebarSolidInvocationInfo {
  handleID: string;
  pipelineName?: string;
}

export type SolidMappingTable = {
  [key: string]: SolidLinkInfo[];
};

export const ShowAllButton = styled.button`
  background: transparent;
  border: none;
  color: ${Colors.BLUE3};
  text-decoration: underline;
  padding-top: 10px;
  font-size: 0.9rem;
`;

export const TypeWrapper = styled.div`
  margin-bottom: 10px;
`;

export const SolidLink = (props: SolidLinkInfo) => (
  <Link to={`./${props.solid.name}`}>
    <Code
      style={{
        display: 'inline-block',
        verticalAlign: 'middle',
        textOverflow: 'ellipsis',
        overflow: 'hidden',
        maxWidth: '100%',
      }}
    >
      {titleOfIO(props)}
    </Code>
  </Link>
);

export const SolidLinks = (props: {title: string; items: SolidLinkInfo[]}) =>
  props.items && props.items.length ? (
    <Text>
      {props.title}
      {props.items.map((i, idx) => (
        <SolidLink key={idx} {...i} />
      ))}
    </Text>
  ) : null;

export const Invocation = (props: {
  invocation: SidebarSolidInvocationInfo;
  onClick: () => void;
}) => {
  const {handleID, pipelineName} = props.invocation;
  const handlePath = handleID.split('.');
  return (
    <InvocationContainer onClick={props.onClick}>
      {pipelineName && <div style={{color: Colors.BLUE1}}>{pipelineName}</div>}
      <SolidColumn stepKey={handlePath.join('.')} />
    </InvocationContainer>
  );
};

export const DependencyRow = ({
  from,
  to,
}: {
  from: SolidLinkInfo | string;
  to: SolidLinkInfo | string;
}) => {
  return (
    <tr>
      <td
        style={{
          whiteSpace: 'nowrap',
          maxWidth: 0,
          width: '45%',
        }}
      >
        {typeof from === 'string' ? (
          <DependencyLocalIOName>{from}</DependencyLocalIOName>
        ) : (
          <SolidLink {...from} />
        )}
      </td>
      <td>
        <img alt="arrow" src={require('./images/icon-dependency-arrow.svg')} />
      </td>
      <td
        style={{
          textOverflow: 'ellipsis',
          overflow: 'hidden',
          whiteSpace: 'nowrap',
          maxWidth: 0,
          width: '60%',
        }}
      >
        {typeof to === 'string' ? (
          <DependencyLocalIOName>{to}</DependencyLocalIOName>
        ) : (
          <SolidLink {...to} />
        )}
      </td>
    </tr>
  );
};

interface DependencyHeaderRowProps {
  label: string;
  style?: React.CSSProperties;
}

export const DependencyHeaderRow: React.FunctionComponent<DependencyHeaderRowProps> = ({
  label,
  ...rest
}) => (
  <tr>
    <DependencyHeaderCell {...rest}>{label}</DependencyHeaderCell>
  </tr>
);

export const ResourceHeader = styled(SectionHeader)`
  font-size: 13px;
`;

export const ResourceContainer = styled.div`
  display: flex;
  align-items: flex-start;
  padding-top: 15px;
  & .bp3-icon {
    padding-top: 7px;
    padding-right: 10px;
  }
  &:first-child {
    padding-top: 0;
  }
`;

export const DependencyLocalIOName = styled.div`
  font-family: monospace;
  font-size: smaller;
  font-weight: 500;
  color: ${Colors.BLACK};
`;

export const DependencyTable = styled.table`
  width: 100%;
`;

export const DependencyHeaderCell = styled.td`
  font-size: 0.7rem;
  color: ${Colors.GRAY3};
`;

export const InvocationContainer = styled.div`
  margin: 0 -10px;
  padding: 10px;
  pointer: default;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY2};
  &:last-child {
    border-bottom: none;
  }
  &:hover {
    background: ${Colors.LIGHT_GRAY5};
  }
  font-family: monospace;
`;
