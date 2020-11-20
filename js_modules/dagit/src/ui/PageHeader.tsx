import {Colors} from '@blueprintjs/core';
import * as React from 'react';

import {Box} from 'src/ui/Box';
import {Heading} from 'src/ui/Text';

interface Props {
  text: React.ReactNode;
}

export const PageHeader = (props: Props) => {
  const {text} = props;
  return (
    <Box
      margin={{bottom: 12}}
      padding={{bottom: 12}}
      border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
    >
      <Heading>{text}</Heading>
    </Box>
  );
};
