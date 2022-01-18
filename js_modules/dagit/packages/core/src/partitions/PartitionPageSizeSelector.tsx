import {ButtonGroup, ButtonGroupItem} from '@dagster-io/ui';
import * as React from 'react';

type Size = '7' | '30' | '120' | 'All';

const labelFor = (size: Size) => {
  switch (size) {
    case '7':
      return 'Last 7';
    case '30':
      return 'Last 30';
    case '120':
      return 'Last 120';
    default:
      return 'All';
  }
};

export const PartitionPageSizeSelector: React.FC<{
  value: number | 'all' | undefined;
  onChange: (value: number | 'all') => void;
}> = ({value, onChange}) => {
  const activeItems: Set<Size> = React.useMemo(
    () => (value === undefined ? new Set() : new Set([`${value}` as Size])),
    [value],
  );
  const onClick = React.useCallback(
    (id: Size) => {
      const idAsInt = parseInt(id);
      onChange(isNaN(idAsInt) ? 'all' : idAsInt);
    },
    [onChange],
  );

  const buttons: ButtonGroupItem<Size>[] = React.useMemo(() => {
    return ['7', '30', '120', 'all'].map((size) => ({
      id: size as Size,
      label: labelFor(size as Size),
    }));
  }, []);

  return <ButtonGroup activeItems={activeItems} buttons={buttons} onClick={onClick} />;
};
