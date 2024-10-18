import {Box} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';

import {CodeLocationSource} from '../CodeLocationSource';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'CodeLocationSource',
  component: CodeLocationSource,
} as Meta;

export const Default = () => {
  return (
    <Box flex={{direction: 'column', gap: 20}}>
      <CodeLocationSource metadata={[]} />
      <CodeLocationSource metadata={[{key: 'url', value: 'not-a-url'}]} />
      <CodeLocationSource
        metadata={[{key: 'url', value: 'https://github.com/dagster-io/dagster'}]}
      />
      <CodeLocationSource metadata={[{key: 'url', value: 'https://gitlab.com/foo-bar'}]} />
      <CodeLocationSource metadata={[{key: 'url', value: 'https://zombo.com'}]} />
    </Box>
  );
};
