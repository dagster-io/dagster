import {Box} from '../Box';
import {Text} from '../Typography';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Typography/Text',
  component: Text,
};

const SIZES = [12, 14, 16, 18, 20, 24, 32] as const;
const WEIGHTS = [400, 500, 600] as const;
const FAMILIES = ['default', 'mono'] as const;
const COLORS = [
  'textDefault',
  'textLight',
  'textLighter',
  'linkDefault',
  'accentRed',
  'accentGreen',
  'accentBlue',
] as const;

export const Basic = () => <Text size={14}>The quick brown fox jumps over the lazy dog</Text>;

export const Sizes = () => (
  <Box flex={{direction: 'column', gap: 12, alignItems: 'flex-start'}}>
    {SIZES.map((size) => (
      <Text key={size} size={size}>
        {`size={${size}}`}
      </Text>
    ))}
  </Box>
);

export const Weights = () => (
  <Box flex={{direction: 'column', gap: 12, alignItems: 'flex-start'}}>
    {WEIGHTS.map((weight) => (
      <Text key={weight} size={14} weight={weight}>
        {`weight={${weight}}`}
      </Text>
    ))}
  </Box>
);

export const Families = () => (
  <Box flex={{direction: 'column', gap: 12, alignItems: 'flex-start'}}>
    {FAMILIES.map((family) => (
      <Text key={family} size={14} family={family}>
        {`family="${family}"`}
      </Text>
    ))}
  </Box>
);

export const Colors = () => (
  <Box flex={{direction: 'column', gap: 12, alignItems: 'flex-start'}}>
    {COLORS.map((color) => (
      <Text key={color} size={14} color={color}>
        {`color="${color}"`}
      </Text>
    ))}
  </Box>
);
