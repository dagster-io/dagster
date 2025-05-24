import * as React from 'react';
import styles from './PageHeader.module.css';

import {Box} from './Box';
import {Colors} from './Color';
import {IconName} from './Icon';

interface Props {
  title?: React.ReactNode;
  tags?: React.ReactNode;
  icon?: IconName;
  description?: React.ReactNode;
  metadata?: React.ReactNode;
  right?: React.ReactNode;
  tabs?: React.ReactNode;
}

export const PageHeader = (props: Props) => {
  const {title, tags, right, tabs} = props;
  return (
    <Box
      className={styles.pageHeaderContainer}
      background={Colors.backgroundLight()}
      padding={{horizontal: 24}}
      border="bottom"
    >
      {title && (
        <Box
          padding={{vertical: 8}}
          style={{minHeight: 52, alignContent: 'center'}}
          flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8}}
        >
          <Box flex={{direction: 'row', alignItems: 'center', gap: 12, wrap: 'wrap'}}>
            {title}
            {tags}
          </Box>
          {right}
        </Box>
      )}
      {tabs}
    </Box>
  );
};
