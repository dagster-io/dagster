// eslint-disable-next-line no-restricted-imports
import {Text} from '@blueprintjs/core';
import {Box, Code, Colors, Icon} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';

import styles from './css/SidebarOpHelpers.module.css';
import {titleOfIO} from '../app/titleOfIO';
import {OpColumn} from '../runs/LogsRowComponents';

type OpLinkInfo = {
  solid: {name: string};
  definition: {name: string};
};

export interface SidebarOpInvocationInfo {
  handleID: string;
  pipelineName?: string;
}

export type OpMappingTable = {
  [key: string]: OpLinkInfo[];
};

export const ShowAllButton = (props: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
  <button {...props} className={styles.showAllButton} />
);

export const TypeWrapper = ({children}: {children: React.ReactNode}) => (
  <div className={styles.typeWrapper}>{children}</div>
);

const OpLink = (props: OpLinkInfo) => (
  <Link to={`./${props.solid.name}`}>
    <Code>{titleOfIO(props)}</Code>
  </Link>
);

export const OpEdges = (props: {title: string; items: OpLinkInfo[]}) =>
  props.items && props.items.length ? (
    <Text>
      {props.title}
      {props.items.map((i, idx) => (
        <OpLink key={idx} {...i} />
      ))}
    </Text>
  ) : null;

export const Invocation = (props: {invocation: SidebarOpInvocationInfo; onClick: () => void}) => {
  const {handleID, pipelineName} = props.invocation;
  const handlePath = handleID.split('.');
  return (
    <div className={styles.invocationContainer} onClick={props.onClick}>
      {pipelineName && <div style={{color: Colors.textBlue()}}>{pipelineName}</div>}
      <OpColumn stepKey={handlePath.join('.')} />
    </div>
  );
};

export const DependencyRow = ({
  from,
  to,
  isDynamic,
}: {
  from: OpLinkInfo | string;
  to: OpLinkInfo | string;
  isDynamic: boolean | null;
}) => {
  return (
    <tr>
      <td className={styles.cell}>
        {typeof from === 'string' ? <Code>{from}</Code> : <OpLink {...from} />}
      </td>
      <td style={{whiteSpace: 'nowrap', textAlign: 'right'}}>
        <Box flex={{direction: 'row', gap: 2, alignItems: 'center'}}>
          {isDynamic && <Icon name="op_dynamic" color={Colors.accentGray()} />}
          <Icon name="arrow_forward" color={Colors.accentGray()} />
        </Box>
      </td>
      <td className={styles.cell}>
        {typeof to === 'string' ? <Code>{to}</Code> : <OpLink {...to} />}
      </td>
    </tr>
  );
};

interface DependencyHeaderRowProps {
  label: string;
  style?: React.CSSProperties;
}

export const DependencyHeaderRow = ({label, ...rest}: DependencyHeaderRowProps) => (
  <tr>
    <td className={styles.dependencyHeaderCell} {...rest}>
      {label}
    </td>
  </tr>
);

export const ResourceHeader = ({children, ...rest}: React.HTMLAttributes<HTMLHeadingElement>) => (
  <h4 className={styles.resourceHeader} {...rest}>
    {children}
  </h4>
);

export const ResourceContainer = ({children}: {children: React.ReactNode}) => (
  <div className={styles.resourceContainer}>{children}</div>
);

export const DependencyTable = ({children}: {children: React.ReactNode}) => (
  <table className={styles.dependencyTable}>{children}</table>
);
