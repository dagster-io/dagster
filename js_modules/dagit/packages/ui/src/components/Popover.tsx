/* eslint-disable @typescript-eslint/no-var-requires */
// eslint-disable-next-line no-restricted-imports
import {Popover2, Popover2Props} from '@blueprintjs/popover2';
import deepmerge from 'deepmerge';
import * as React from 'react';
import {createGlobalStyle} from 'styled-components/macro';

import searchSVG from '../icon-svgs/search.svg';

import {Colors} from './Colors';
import {FontFamily} from './styles';

export const GlobalPopoverStyle = createGlobalStyle`
  .dagit-popover.bp4-popover2,
  .dagit-popover.bp4-popover {
    box-shadow: rgba(0, 0, 0, 0.12) 0px 2px 12px;
  }

  .dagit-popover .bp4-popover2-content,
  .dagit-popover .bp4-popover-content {
    border-radius: 4px;

    .bp4-input-group {
      .bp4-icon.bp4-icon-search {
        width: 16px;
        height: 16px;
        background: ${Colors.Gray900};
        mask-image: url(${searchSVG});
        mask-size: cover;
        &::before { 
          content: '';
        }
        svg {
          display: none;
        }
      }
        
      .bp4-input {
        border: none;
        border-radius: 8px;
        box-shadow: ${Colors.Gray300} inset 0px 0px 0px 1px, ${Colors.KeylineGray} inset 2px 2px 1.5px;
        font-family: ${FontFamily.default};
        ::placeholder {
          color: ${Colors.Gray500};
        }
      }
    }
  }

  .dagit-popover .bp4-popover2-content > :first-child {
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
  }

  .dagit-popover .bp4-popover2-content > :last-child {
    border-bottom-left-radius: 4px;
    border-bottom-right-radius: 4px;
  }

  .dagit-popover .bp4-popover2-arrow-fill {
    fill: ${Colors.Gray900};
  }
  .dagit-popover .bp4-popover2.bp4-dark .bp4-popover2-content,
  .bp4-dark .dagit-popover .bp4-popover2 .bp4-popover2-content {
    background-color: ${Colors.Gray900};
  }
`;

// Overwrite arrays instead of concatting them.
const overwriteMerge = (destination: any[], source: any[]) => source;

interface Props extends Popover2Props {
  children: React.ReactNode;
}

export const Popover = (props: Props) => {
  return (
    <Popover2
      minimal
      autoFocus={false}
      {...props}
      popoverClassName={`dagit-popover ${props.popoverClassName}`}
      modifiers={deepmerge(
        {offset: {enabled: true, options: {offset: [0, 8]}}},
        props.modifiers || {},
        {arrayMerge: overwriteMerge},
      )}
    />
  );
};
