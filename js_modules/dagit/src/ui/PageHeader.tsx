import {Colors, Icon, IconName} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';

interface Props {
  title: React.ReactNode;
  icon?: IconName;
  description?: React.ReactNode;
  metadata?: React.ReactNode;
  right?: React.ReactNode;
}

export const PageHeader = (props: Props) => {
  const {title, icon, description, metadata, right} = props;
  return (
    <Box flex={{direction: 'row', justifyContent: 'space-between'}} style={{width: '100%'}}>
      <Box flex={{direction: 'row', alignItems: 'flex-start'}}>
        <Group direction="column" spacing={8}>
          {title}
          <Group direction="row" spacing={4} alignItems="center">
            <Icon
              color={Colors.GRAY1}
              icon={icon}
              iconSize={10}
              style={{position: 'relative', top: -3}}
            />
            <Description>{description}</Description>
          </Group>
        </Group>
        {metadata ? (
          <Box
            border={{side: 'left', width: 1, color: Colors.LIGHT_GRAY3}}
            padding={{horizontal: 20}}
            margin={{left: 20}}
          >
            {metadata}
          </Box>
        ) : null}
      </Box>
      {right || null}
    </Box>
  );
};

const Description = styled.div`
  color: ${Colors.GRAY3};

  a,
  a:link,
  a:visited,
  a:hover,
  a:active {
    color: ${Colors.GRAY2};
    font-weight: 500;
  }

  .bp3-breadcrumbs > li::after {
    height: 12px;
    width: 12px;
    margin: 0 2px;
  }
`;
