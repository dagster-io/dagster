import * as React from 'react';
import styled from 'styled-components/macro';

import {ShortcutHandler} from '../app/ShortcutHandler';
import {ButtonWIP} from '../ui/Button';
import {IconWIP} from '../ui/Icon';
import {MenuItemWIP} from '../ui/Menu';
import {SelectWIP} from '../ui/Select';

import {GraphExplorerSolidHandleFragment_solid} from './types/GraphExplorerSolidHandleFragment';

interface SolidJumpBarProps {
  solids: Array<GraphExplorerSolidHandleFragment_solid>;
  selectedSolid: GraphExplorerSolidHandleFragment_solid | undefined;
  onChange: (solid: GraphExplorerSolidHandleFragment_solid) => void;
}

export const SolidJumpBar: React.FC<SolidJumpBarProps> = (props) => {
  const {solids, selectedSolid, onChange} = props;
  const button = React.useRef<HTMLButtonElement | null>(null);

  return (
    <ShortcutHandler
      onShortcut={() => button.current?.click()}
      shortcutLabel="⌥S"
      shortcutFilter={(e) => e.code === 'KeyS' && e.altKey}
    >
      <SelectWIP
        items={solids.map((s) => s.name)}
        itemRenderer={BasicStringRenderer}
        itemListPredicate={BasicStringPredicate}
        noResults={<MenuItemWIP disabled text="No results." />}
        onItemSelect={(name) => onChange(solids.find((s) => s.name === name)!)}
      >
        <SelectButton ref={button} rightIcon={<IconWIP name="unfold_more" />}>
          {selectedSolid ? selectedSolid.name : 'Select an op…'}
        </SelectButton>
      </SelectWIP>
    </ShortcutHandler>
  );
};

// By default, Blueprint's Select component has an intrinsic size determined by the length of
// it's content, which in our case can be wildly long and unruly. Giving the Select a min-width
// of 0px and adding "width" rules to all nested <divs> that are a function of the parent (eg: 100%)
// tells the layout engine that this can be assigned a width by it's container. This allows
// us to make the Select "as wide as the layout allows" and have it truncate first.
const SelectButton = styled(ButtonWIP)`
  min-width: 0;

  && {
    max-width: 100%;
    white-space: nowrap;
  }

  & .bp3-button-text {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
  }
`;

const BasicStringPredicate = (text: string, items: string[]) =>
  items.filter((i) => i.toLowerCase().includes(text.toLowerCase())).slice(0, 20);

const BasicStringRenderer = (item: string, options: {handleClick: any; modifiers: any}) => (
  <MenuItemWIP
    key={item}
    text={item}
    active={options.modifiers.active}
    onClick={options.handleClick}
  />
);
