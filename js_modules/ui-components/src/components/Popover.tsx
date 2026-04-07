// eslint-disable-next-line no-restricted-imports
import {
  Popover as BlueprintPopover,
  PopoverProps as BlueprintPopoverProps,
} from '@blueprintjs/core';
import deepmerge from 'deepmerge';
import {css} from 'styled-components';

import {Colors} from './Color';

export const PopoverWrapperStyle = css`
  box-shadow: ${Colors.shadowDefault()} 0px 2px 12px;
`;

export const PopoverContentStyle = css`
  background-color: ${Colors.popoverBackground()};
  border-radius: 4px;

  > :first-child {
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
  }

  > :last-child {
    border-bottom-left-radius: 4px;
    border-bottom-right-radius: 4px;
  }
`;

// Overwrite arrays instead of concatting them.
const overwriteMerge = (destination: any[], source: any[]) => source;

export const Popover = (props: BlueprintPopoverProps) => {
  return (
    <BlueprintPopover
      minimal
      autoFocus={false}
      enforceFocus={false}
      {...props}
      popoverClassName={`dagster-popover ${props.popoverClassName}`}
      modifiers={deepmerge(
        {offset: {enabled: true, options: {offset: [0, 8]}}},
        props.modifiers || {},
        {arrayMerge: overwriteMerge},
      )}
    />
  );
};
