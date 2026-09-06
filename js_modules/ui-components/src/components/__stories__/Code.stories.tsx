import {Box} from '../Box';
import {Code} from '../Code';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Code',
  component: Code,
};

export const Basic = () => (
  <Box flex={{direction: 'column', gap: 12, alignItems: 'flex-start'}}>
    <div>
      Run <Code>dagster dev</Code> to start the local development server.
    </div>
    <div>
      Install with <Code>uv add dagster</Code> and import <Code>dagster</Code>.
    </div>
  </Box>
);
