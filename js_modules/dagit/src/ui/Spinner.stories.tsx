import {Colors} from '@blueprintjs/core';
import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {Spinner} from 'src/ui/Spinner';
import {Caption, Code} from 'src/ui/Text';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Spinner',
  component: Spinner,
} as Meta;

export const Sizes = () => {
  return (
    <Group direction="column" spacing={32}>
      <Box padding={20} border={{side: 'all', width: 1, color: Colors.LIGHT_GRAY3}}>
        <Group direction="column" spacing={16}>
          <Code>{`purpose="caption-text"`}</Code>
          <Group direction="row" spacing={8} alignItems="center">
            <Spinner purpose="caption-text" />
            <Caption>Waiting for something to load…</Caption>
          </Group>
        </Group>
      </Box>
      <Box padding={20} border={{side: 'all', width: 1, color: Colors.LIGHT_GRAY3}}>
        <Group direction="column" spacing={16}>
          <Code>{`purpose="body-text"`}</Code>
          <Group direction="row" spacing={8} alignItems="center">
            <Spinner purpose="body-text" />
            <div>Waiting for something to load…</div>
          </Group>
        </Group>
      </Box>
      <Box padding={20} border={{side: 'all', width: 1, color: Colors.LIGHT_GRAY3}}>
        <Group direction="column" spacing={16}>
          <Code>{`purpose="section"`}</Code>
          <Box flex={{direction: 'row', justifyContent: 'center'}} padding={24}>
            <Spinner purpose="section" />
          </Box>
        </Group>
      </Box>
      <Box padding={20} border={{side: 'all', width: 1, color: Colors.LIGHT_GRAY3}}>
        <Group direction="column" spacing={16}>
          <Code>{`purpose="page"`}</Code>
          <Box flex={{direction: 'row', justifyContent: 'center'}} padding={48}>
            <Spinner purpose="page" />
          </Box>
        </Group>
      </Box>
    </Group>
  );
};
