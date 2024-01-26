import {Icon} from './Icon';
import {UnstyledButton} from './UnstyledButton';

type Props = {
  isOpen: boolean;
  onToggle: (e: React.MouseEvent<HTMLButtonElement>) => void;
};
export const ToggleButton = ({isOpen, onToggle}: Props) => {
  return (
    <UnstyledButton
      onClick={(e) => {
        onToggle(e);
      }}
      onKeyDown={(e) => {
        if (e.code === 'Space') {
          // Prevent the default scrolling behavior
          e.preventDefault();
        }
      }}
      style={{cursor: 'pointer', width: 18}}
    >
      <Icon
        name="arrow_drop_down"
        style={{transform: isOpen ? 'rotate(0deg)' : 'rotate(-90deg)'}}
      />
    </UnstyledButton>
  );
};
