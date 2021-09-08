import {Button, MenuItem} from '@blueprintjs/core';
import {Select} from '@blueprintjs/select';
import * as React from 'react';
import * as ReactDOM from 'react-dom';
import styled from 'styled-components/macro';

import {useFeatureFlags} from '../app/Flags';
import {ShortcutHandler} from '../app/ShortcutHandler';

import {PipelineExplorerSolidHandleFragment_solid} from './types/PipelineExplorerSolidHandleFragment';

interface SolidJumpBarProps {
  solids: Array<PipelineExplorerSolidHandleFragment_solid>;
  selectedSolid: PipelineExplorerSolidHandleFragment_solid | undefined;
  onChange: (solid: PipelineExplorerSolidHandleFragment_solid) => void;
}

export const SolidJumpBar: React.FC<SolidJumpBarProps> = (props) => {
  const {flagPipelineModeTuples} = useFeatureFlags();
  const select = React.useRef<Select<string>>(null);
  const {solids, selectedSolid, onChange} = props;

  return (
    <ShortcutHandler
      onShortcut={() => activateSelect(select.current)}
      shortcutLabel="⌥S"
      shortcutFilter={(e) => e.code === 'KeyS' && e.altKey}
    >
      <StringSelectNoIntrinsicWidth
        ref={select}
        items={solids.map((s) => s.name)}
        itemRenderer={BasicStringRenderer}
        itemListPredicate={BasicStringPredicate}
        noResults={<MenuItem disabled={true} text="No results." />}
        onItemSelect={(name) => onChange(solids.find((s) => s.name === name)!)}
      >
        <Button
          text={
            selectedSolid
              ? selectedSolid.name
              : flagPipelineModeTuples
              ? 'Select an op…'
              : 'Select a solid…'
          }
          rightIcon="double-caret-vertical"
        />
      </StringSelectNoIntrinsicWidth>
    </ShortcutHandler>
  );
};

// By default, Blueprint's Select component has an intrinsic size determined by the length of
// it's content, which in our case can be wildly long and unruly. Giving the Select a min-width
// of 0px and adding "width" rules to all nested <divs> that are a function of the parent (eg: 100%)
// tells the layout engine that this can be assigned a width by it's container. This allows
// us to make the Select "as wide as the layout allows" and have it truncate first.
//
const StringSelectNoIntrinsicWidth = styled(Select.ofType<string>())`
  min-width: 0;

  & .bp3-popover-target {
    width: 100%;
  }
  & .bp3-button {
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
  <MenuItem
    key={item}
    text={item}
    active={options.modifiers.active}
    onClick={options.handleClick}
  />
);

function activateSelect(select: Select<any> | null) {
  if (!select) {
    return;
  }
  // eslint-disable-next-line react/no-find-dom-node
  const selectEl = ReactDOM.findDOMNode(select) as HTMLElement;
  const btnEl = selectEl.querySelector('button');
  if (btnEl) {
    btnEl.click();
  }
}
