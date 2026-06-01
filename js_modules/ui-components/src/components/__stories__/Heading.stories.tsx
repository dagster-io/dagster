import {Box} from '../Box';
import {Heading} from '../Typography';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Typography/Heading',
  component: Heading,
};

const SIZES = [12, 14, 16, 18, 20, 24, 32] as const;
const WEIGHTS = [500, 600] as const;
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

export const Basic = () => (
  <Heading size={20} weight={500}>
    The quick brown fox jumps over the lazy dog
  </Heading>
);

export const Sizes = () => (
  <Box flex={{direction: 'column', gap: 12, alignItems: 'flex-start'}}>
    {SIZES.map((size) => (
      <Heading key={size} size={size} weight={500}>
        {`size={${size}}`}
      </Heading>
    ))}
  </Box>
);

export const Weights = () => (
  <Box flex={{direction: 'column', gap: 12, alignItems: 'flex-start'}}>
    {WEIGHTS.map((weight) => (
      <Heading key={weight} size={16} weight={weight}>
        {`weight={${weight}}`}
      </Heading>
    ))}
  </Box>
);

export const Families = () => (
  <Box flex={{direction: 'column', gap: 12, alignItems: 'flex-start'}}>
    {FAMILIES.map((family) => (
      <Heading key={family} size={16} weight={500} family={family}>
        {`family="${family}"`}
      </Heading>
    ))}
  </Box>
);

export const Colors = () => (
  <Box flex={{direction: 'column', gap: 12, alignItems: 'flex-start'}}>
    {COLORS.map((color) => (
      <Heading key={color} size={16} weight={500} color={color}>
        {`color="${color}"`}
      </Heading>
    ))}
  </Box>
);
