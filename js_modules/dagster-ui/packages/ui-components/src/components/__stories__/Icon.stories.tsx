import {CoreColors} from '../../palettes/CoreColors';
import {Box} from '../Box';
import {Colors} from '../Color';
import {Icon, IconNames as _iconNames} from '../Icon';
import {Tooltip} from '../Tooltip';

const IconNames = _iconNames.slice().sort();

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Icon',
  component: Icon,
};

export const Size16 = () => {
  return (
    <Box flex={{gap: 6, wrap: 'wrap'}}>
      {IconNames.map((name) => (
        <Tooltip content={name} key={name}>
          <Icon name={name} />
        </Tooltip>
      ))}
    </Box>
  );
};

export const Size24 = () => {
  return (
    <Box flex={{gap: 6, wrap: 'wrap'}}>
      {IconNames.map((name) => (
        <Tooltip content={name} key={name}>
          <Icon name={name} size={24} />
        </Tooltip>
      ))}
    </Box>
  );
};

export const IconColors = () => {
  const colorKeys = Object.keys(CoreColors);
  const numColors = colorKeys.length;
  const colorAtIndex = (index: number) => {
    const colorKey = colorKeys[index % numColors];
    if (colorKey) {
      const colorAtKey = CoreColors[colorKey as keyof typeof CoreColors];
      if (colorAtKey) {
        return colorAtKey;
      }
    }
    return Colors.accentWhite();
  };

  return (
    <Box flex={{gap: 6, wrap: 'wrap'}}>
      {IconNames.map((name, idx) => (
        <Tooltip content={name} key={name}>
          <Icon name={name} color={colorAtIndex(idx)} size={24} />
        </Tooltip>
      ))}
    </Box>
  );
};
