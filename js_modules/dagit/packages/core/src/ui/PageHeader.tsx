import * as React from 'react';

import {Box} from './Box';
import {ColorsWIP} from './Colors';
import {IconName} from './Icon';

interface Props {
  title: React.ReactNode;
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
      background={ColorsWIP.Gray50}
      padding={{top: 16, left: 24, right: 12}}
      border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
      style={{width: '100%'}}
    >
      <Box flex={{direction: 'row', justifyContent: 'space-between'}} padding={{bottom: 16}}>
        <Box flex={{direction: 'row', alignItems: 'flex-start', gap: 12}}>
          {title}
          {tags}
        </Box>
        {right}
      </Box>
      {tabs}
    </Box>
  );
};
