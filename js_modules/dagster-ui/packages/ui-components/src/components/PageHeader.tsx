import * as React from 'react';
import styled from 'styled-components';

import {colorBackgroundLight} from '../theme/color';

import {Box} from './Box';
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
      background={colorBackgroundLight()}
      padding={{top: 16, left: 24, right: 12}}
      border="bottom"
    >
      <Box flex={{direction: 'row', justifyContent: 'space-between'}} padding={{bottom: 16}}>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 12, wrap: 'wrap'}}>
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
  .bp4-breadcrumbs {
    height: auto;
  }
`;
