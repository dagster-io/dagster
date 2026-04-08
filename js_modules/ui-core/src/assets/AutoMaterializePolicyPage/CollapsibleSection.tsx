import {Box, Colors, Icon, Subheading, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';

import styles from './css/CollapsibleSection.module.css';

interface Props {
  header: React.ReactNode;
  details: JSX.Element | string;
  headerRightSide?: React.ReactNode;
  children: React.ReactNode;
}

export const CollapsibleSection = ({header, details, headerRightSide, children}: Props) => {
  return (
    <Collapsible
      header={
        <Box
          flex={{
            justifyContent: 'space-between',
            gap: 12,
            grow: 1,
          }}
        >
          <Box flex={{direction: 'row', alignItems: 'center', gap: 8, grow: 1}}>
            <Subheading>{header}</Subheading>
            {details ? (
              <Tooltip content={details} placement="top">
                <Icon color={Colors.accentGray()} name="info" />
              </Tooltip>
            ) : null}
          </Box>
          {headerRightSide}
        </Box>
      }
    >
      <Box padding={{vertical: 12, left: 32, right: 16}}>{children}</Box>
    </Collapsible>
  );
};

export const Collapsible = ({
  header,
  children,
}: {
  header: React.ReactNode;
  children: React.ReactNode;
}) => {
  const [isCollapsed, setIsCollapsed] = React.useState(false);
  return (
    <Box flex={{direction: 'column'}} border="bottom">
      <button className={styles.sectionHeader} onClick={() => setIsCollapsed(!isCollapsed)}>
        <Box
          flex={{direction: 'row', alignItems: 'center', gap: 6}}
          padding={{vertical: 8, horizontal: 12}}
          border="bottom"
        >
          <Icon
            name="arrow_drop_down"
            style={{transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)'}}
          />
          <div>{header}</div>
        </Box>
      </button>
      {isCollapsed ? null : children}
    </Box>
  );
};
