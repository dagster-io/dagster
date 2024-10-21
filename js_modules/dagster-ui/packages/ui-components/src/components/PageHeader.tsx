import * as React from 'react';
import styled from 'styled-components';

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
    <PageHeaderContainer
      background={Colors.backgroundLight()}
      padding={{horizontal: 24}}
      border="bottom"
    >
      {title && (
        <Box
          style={{minHeight: 52, alignContent: 'center'}}
          flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
        >
          <Box flex={{direction: 'row', alignItems: 'center', gap: 12, wrap: 'wrap'}}>
            {title}
            {tags}
          </Box>
          {right}
        </Box>
      )}
      {tabs}
    </PageHeaderContainer>
  );
};

const PageHeaderContainer = styled(Box)`
  width: 100%;

  /**
   * Blueprint breadcrumbs annoyingly have a built-in height.
   */
  .bp5-breadcrumbs {
    height: auto;
  }
`;
