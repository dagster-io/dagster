import {useState} from 'react';

import {CoreColors} from '../../palettes/CoreColors';
import {Box} from '../Box';
import {Colors} from '../Color';
import {Icon, IconName, IconNames as _iconNames} from '../Icon';
import {TextInput} from '../TextInput';
import {Tooltip} from '../Tooltip';

const IconNames = _iconNames.slice().sort();

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Icon',
  component: Icon,
};

const IconGallery = ({
  renderIcon,
}: {
  renderIcon: (name: IconName, index: number) => React.ReactNode;
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const searchLower = searchQuery.toLowerCase();
  const filtered = IconNames.filter((name) => name.toLowerCase().includes(searchLower));

  return (
    <Box flex={{direction: 'column', gap: 12}}>
      <Box flex={{direction: 'column', gap: 8}} style={{maxWidth: 300}}>
        <TextInput
          icon="search"
          placeholder="Search icons…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <span style={{fontSize: 12, color: Colors.textLight()}}>
          {filtered.length} of {IconNames.length} icons
        </span>
      </Box>
      <Box flex={{gap: 6, wrap: 'wrap'}}>
        {filtered.map((name, idx) => (
          <Tooltip content={name} key={name}>
            {renderIcon(name, idx)}
          </Tooltip>
        ))}
      </Box>
    </Box>
  );
};

export const Size16 = () => {
  return <IconGallery renderIcon={(name) => <Icon name={name} />} />;
};

export const Size24 = () => {
  return <IconGallery renderIcon={(name) => <Icon name={name} size={24} />} />;
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
    <IconGallery
      renderIcon={(name, idx) => <Icon name={name} color={colorAtIndex(idx)} size={24} />}
    />
  );
};
