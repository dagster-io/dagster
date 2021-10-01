import * as React from 'react';
import styled from 'styled-components/macro';

import {Box} from './Box';
import {ColorsWIP} from './Colors';
import {Group} from './Group';
import {IconName, IconWIP} from './Icon';

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
            {icon ? <IconWIP color={ColorsWIP.Gray400} name={icon} /> : null}
            <Description>{description}</Description>
          </Group>
        </Group>
        {metadata ? (
          <Box
            border={{side: 'left', width: 1, color: ColorsWIP.Gray100}}
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
  color: ${ColorsWIP.Gray400};
  white-space: nowrap;

  a,
  a:link,
  a:visited,
  a:hover,
  a:active {
    color: ${ColorsWIP.Gray500};
    font-weight: 500;
  }

  .bp3-breadcrumbs > li::after {
    height: 12px;
    width: 12px;
    margin: 0 2px;
  }
`;
