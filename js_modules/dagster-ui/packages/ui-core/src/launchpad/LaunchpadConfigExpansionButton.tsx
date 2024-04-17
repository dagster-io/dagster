import {Button, Icon} from '@dagster-io/ui-components';
import {useState} from 'react';

interface Props {
  axis: 'horizontal' | 'vertical';
  firstInitialPercent: number;
  getSize?: () => number;
  changeSize?: (value: number) => void;
}

export const LaunchpadConfigExpansionButton = ({
  axis,
  firstInitialPercent,
  getSize,
  changeSize,
}: Props) => {
  const [prevSize, setPrevSize] = useState<number | 'unknown'>('unknown');
  const [open, setOpen] = useState<boolean>(() => {
    const size = getSize ? getSize() : 0;
    return size < 100;
  });

  const onClick = () => {
    if (!getSize || !changeSize) {
      return;
    }

    const size = getSize();
    if (size < 90) {
      setPrevSize(size);
      setOpen(false);
      changeSize(100);
    } else {
      setOpen(true);
      changeSize(prevSize === 'unknown' ? firstInitialPercent : prevSize);
    }
  };

  const icon = (
    <Icon
      name={
        axis === 'horizontal'
          ? open
            ? 'panel_hide_right'
            : 'panel_show_right'
          : 'panel_show_bottom'
      }
    />
  );

  return <Button active={open} title="Toggle second pane" icon={icon} onClick={onClick} />;
};
