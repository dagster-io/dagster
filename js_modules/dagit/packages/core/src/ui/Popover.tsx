// eslint-disable-next-line no-restricted-imports
import {Popover2, Popover2Props} from '@blueprintjs/popover2';
import deepmerge from 'deepmerge';
import * as React from 'react';
import {createGlobalStyle} from 'styled-components/macro';

import {ColorsWIP} from './Colors';

export const GlobalPopoverStyle = createGlobalStyle`
  .dagit-popover.bp3-popover2,
  .dagit-popover.bp3-popover {
    box-shadow: rgba(0, 0, 0, 0.12) 0px 2px 12px;
  }

  .dagit-popover .bp3-popover2-content,
  .dagit-popover .bp3-popover-content {
    border-radius: 4px;
  }

  .dagit-popover .bp3-popover2-content > :first-child {
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
  }

  .dagit-popover .bp3-popover2-content > :last-child {
    border-bottom-left-radius: 4px;
    border-bottom-right-radius: 4px;
  }

  .dagit-popover .bp3-popover2.bp3-dark .bp3-popover2-content,
  .bp3-dark .dagit-popover .bp3-popover2 .bp3-popover2-content {
    background-color: ${ColorsWIP.Gray900};
  }
`;

// Overwrite arrays instead of concatting them.
const overwriteMerge = (destination: any[], source: any[]) => source;

export const Popover: React.FC<Popover2Props> = (props) => {
  return (
    <Popover2
      {...props}
      minimal
      autoFocus={false}
      popoverClassName={`dagit-popover ${props.popoverClassName}`}
      modifiers={deepmerge(
        {offset: {enabled: true, options: {offset: [0, 8]}}},
        props.modifiers || {},
        {arrayMerge: overwriteMerge},
      )}
    />
  );
};
