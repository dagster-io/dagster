import {Popover2, Popover2Props} from '@blueprintjs/popover2';
import deepmerge from 'deepmerge';
import * as React from 'react';
import {createGlobalStyle} from 'styled-components/macro';

export const GlobalPopoverStyle = createGlobalStyle`
  .dagit-popover.bp3-popover2,
  .dagit-popover.bp3-popover {
    box-shadow: rgba(0, 0, 0, 0.12) 0px 2px 12px;
  }

  .dagit-popover .bp3-popover2-content,
  .dagit-popover .bp3-popover-content {
    border-radius: 4px;
  }
`;

export const Popover: React.FC<Popover2Props> = (props) => {
  return (
    <Popover2
      {...props}
      minimal
      popoverClassName={`dagit-popover ${props.popoverClassName}`}
      modifiers={deepmerge(
        {offset: {enabled: true, options: {offset: [0, 8]}}},
        props.modifiers || {},
      )}
    />
  );
};
