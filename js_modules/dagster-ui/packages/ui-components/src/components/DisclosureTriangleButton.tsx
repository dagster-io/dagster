import {Icon} from './Icon';
import {UnstyledButton} from './UnstyledButton';

type Props = {
  isOpen: boolean;
  onToggle: (e: React.MouseEvent<HTMLButtonElement>) => void;
};
export const DisclosureTriangleButton = ({isOpen, onToggle}: Props) => {
  return (
    <UnstyledButton
      onClick={(e) => {
        onToggle(e);
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
