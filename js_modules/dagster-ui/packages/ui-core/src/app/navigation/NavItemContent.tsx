import {Box} from '@dagster-io/ui-components';
import {ReactNode} from 'react';

interface Props {
  icon: ReactNode;
  label?: string;
  collapsed: boolean;
  rightIcon?: ReactNode;
}

export const NavItemContent = ({icon, label, collapsed, rightIcon}: Props) => {
  if (collapsed) {
    return (
      <Box flex={{alignItems: 'center', justifyContent: 'center'}} padding={8}>
        <div>{icon}</div>
      </Box>
    );
  }

  return (
    <Box
      flex={{direction: 'row', alignItems: 'center', gap: 8}}
      padding={{vertical: 8, horizontal: 12}}
    >
      <div>{icon}</div>
      {label && <div>{label}</div>}
      {typeof rightIcon === 'object' && rightIcon !== null ? <div>{rightIcon}</div> : null}
    </Box>
  );
};
