import * as React from 'react';
import styled from 'styled-components/macro';

import {Box} from './Box';
import {Colors} from './Colors';
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
    <PageHeaderContainer
      background={Colors.Gray50}
      padding={{top: 16, left: 24, right: 12}}
      border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
    >
      <Box flex={{direction: 'row', justifyContent: 'space-between'}} padding={{bottom: 16}}>
        <Box flex={{direction: 'row', alignItems: 'flex-start', gap: 12, wrap: 'wrap'}}>
          {title}
          {tags}
        </Box>
        {right}
      </Box>
      {tabs}
    </PageHeaderContainer>
  );
};

const PageHeaderContainer = styled(Box)`
  width: 100%;

  /**
   * Blueprint breadcrumbs annoyingly have a built-in height.
   */
  .bp3-breadcrumbs {
    height: auto;
  }
`;
