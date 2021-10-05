import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {ButtonGroup, ButtonGroupItem} from './ButtonGroup';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'ButtonGroup',
  component: ButtonGroup,
} as Meta;

export const Multiple = () => {
  const [activeItems, setActiveItems] = React.useState<Set<string>>(() => new Set());
  const onClick = React.useCallback((id: string) => {
    setActiveItems((current) => {
      const copy = new Set(current);
      copy.has(id) ? copy.delete(id) : copy.add(id);
      return copy;
    });
  }, []);

  const buttons: ButtonGroupItem<string>[] = [
    {id: 'split', icon: 'splitscreen'},
    {id: 'top', icon: 'vertical_align_top'},
    {id: 'bottom', icon: 'vertical_align_bottom'},
  ];

  return <ButtonGroup activeItems={activeItems} buttons={buttons} onClick={onClick} />;
};

export const Single = () => {
  const [activeItems, setActiveItems] = React.useState<Set<string>>(() => new Set());
  const onClick = React.useCallback((id: string) => {
    setActiveItems(new Set([id]));
  }, []);

  const buttons: ButtonGroupItem<string>[] = [
    {id: 'split', icon: 'splitscreen', label: 'Split'},
    {id: 'top', icon: 'vertical_align_top', label: 'Top'},
    {id: 'bottom', icon: 'vertical_align_bottom', label: 'Bottom'},
  ];

  return <ButtonGroup activeItems={activeItems} buttons={buttons} onClick={onClick} />;
};
