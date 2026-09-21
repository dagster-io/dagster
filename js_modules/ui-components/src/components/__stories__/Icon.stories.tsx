import {useState} from 'react';

import {Box} from '../Box';
import {Colors} from '../Color';
import {Icon, IconName, IconNames as _iconNames} from '../Icon';
import {TextInput} from '../TextInput';
import {UnstyledButton} from '../UnstyledButton';

const IconNames = _iconNames.slice().sort();

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Icon',
  component: Icon,
};

const CopyableText = ({text}: {text: string}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  const handleClick = () => {
    navigator.clipboard.writeText(text);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <UnstyledButton
      style={{
        fontSize: '14px',
        lineHeight: '16px',
        color: Colors.textLight(),
        cursor: 'pointer',
        display: 'flex',
        gap: '4px',
        alignItems: 'center',
      }}
      onClick={handleClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {text}
      {isCopied ? (
        <Icon name="copy_to_clipboard_done" size={16} />
      ) : (
        isHovered && <Icon name="copy_to_clipboard" size={16} />
      )}
    </UnstyledButton>
  );
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
      <Box
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gridTemplateRows: `repeat(${Math.ceil(filtered.length / 4)}, auto)`,
          gridGap: '8px',
          gridAutoFlow: 'column',
        }}
      >
        {filtered.map((name, idx) => (
          <Box key={name} flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
            {renderIcon(name, idx)}
            <CopyableText text={name} />
          </Box>
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
  const colorFns = Object.values(Colors).filter((v): v is () => string => typeof v === 'function');
  const numColors = colorFns.length;
  const colorAtIndex = (index: number) => {
    const fn = colorFns[index % numColors];
    return fn ? fn() : Colors.accentWhite();
  };

  return (
    <IconGallery
      renderIcon={(name, idx) => <Icon name={name} color={colorAtIndex(idx)} size={24} />}
    />
  );
};
