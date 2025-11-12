import {Icon, UnstyledButton} from '@dagster-io/ui-components';

export const SidebarDisclosureTriangle = ({
  isOpen,
  toggleOpen,
}: {
  isOpen: boolean;
  toggleOpen: () => void;
}) => (
  <UnstyledButton
    onClick={(e) => {
      e.stopPropagation();
      toggleOpen();
    }}
    onDoubleClick={(e) => {
      e.stopPropagation();
    }}
    onKeyDown={(e) => {
      if (e.code === 'Space') {
        // Prevent the default scrolling behavior
        e.preventDefault();
      }
    }}
    style={{cursor: 'pointer', width: 18, flexShrink: 0}}
  >
    <Icon name="arrow_drop_down" style={{transform: isOpen ? 'rotate(0deg)' : 'rotate(-90deg)'}} />
  </UnstyledButton>
);
