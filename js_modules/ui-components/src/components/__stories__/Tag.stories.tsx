import {Box} from '../Box';
import {Tag} from '../Tag';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Tag',
  component: Tag,
};

const INTENTS = ['none', 'primary', 'success', 'warning', 'danger'] as any[];

export const Basic = () => {
  return (
    <Box flex={{direction: 'column', gap: 8}}>
      {INTENTS.map((intent) => (
        <Box flex={{direction: 'row', gap: 8}} key={intent}>
          <Tag intent={intent} icon="info" />
          <Tag intent={intent} icon="alternate_email">
            Lorem
          </Tag>
          <Tag intent={intent} rightIcon="toggle_off">
            Lorem
          </Tag>
          <Tag intent={intent}>Lorem</Tag>
        </Box>
      ))}
    </Box>
  );
};

export const Loading = () => {
  return (
    <Box flex={{direction: 'column', gap: 8}}>
      {INTENTS.map((intent) => (
        <Box flex={{direction: 'row', gap: 8}} key={intent}>
          <Tag intent={intent} icon="alternate_email" rightIcon="spinner">
            Lorem
          </Tag>
          <Tag intent={intent} icon="spinner" rightIcon="toggle_off">
            Lorem
          </Tag>
          <Tag intent={intent} icon="spinner">
            Lorem
          </Tag>
        </Box>
      ))}
    </Box>
  );
};
