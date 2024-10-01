/* eslint-disable @typescript-eslint/no-var-requires */
// eslint-disable-next-line no-restricted-imports
import {Popover2, Popover2Props} from '@blueprintjs/popover2';
import deepmerge from 'deepmerge';
import * as React from 'react';
import {createGlobalStyle} from 'styled-components';

import {Colors} from './Color';
import {FontFamily} from './styles';
import searchSVG from '../icon-svgs/search.svg';

export const GlobalPopoverStyle = createGlobalStyle`
  .dagster-popover.bp5-popover,
  .dagster-popover.bp5-popover {
    box-shadow: ${Colors.shadowDefault()} 0px 2px 12px;
  }

  .dagster-popover .bp5-popover-content,
  .dagster-popover .bp5-popover-content {
    background-color: ${Colors.popoverBackground()};
    border-radius: 4px;

    .bp5-menu {
      background-color: ${Colors.popoverBackground()};
      color: ${Colors.textDefault()};
    }

    .bp5-input-group {
      .bp5-icon.bp5-icon-search {
        width: 16px;
        height: 16px;
        background: ${Colors.accentGray()};
        mask-image: url(${searchSVG.src});
        mask-size: cover;
        &::before { 
          content: '';
        }
        svg {
          display: none;
        }
      }
        
      .bp5-input {
        background-color: ${Colors.popoverBackground()};
        border: none;
        border-radius: 8px;
        box-shadow: ${Colors.borderDefault()} inset 0px 0px 0px 1px, ${Colors.keylineDefault()} inset 2px 2px 1.5px;
        color: ${Colors.textDefault()};
        font-family: ${FontFamily.default};
        ::placeholder {
          color: ${Colors.textDisabled()};
        }
      }
    }
  }

  .dagster-popover .bp5-popover-content > :first-child {
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
  }

  .dagster-popover .bp5-popover-content > :last-child {
    border-bottom-left-radius: 4px;
    border-bottom-right-radius: 4px;
  }

  .dagster-popover .bp5-popover-arrow-fill {
    fill: ${Colors.popoverBackground()};
  }

  .dagster-popover.bp5-dark .bp5-popover-arrow-fill {
    fill: ${Colors.tooltipBackground()};
  }

  .dagster-popover.bp5-dark .bp5-popover-arrow-border {
    fill: ${Colors.shadowDefault()};
    fill-opacity: 0.7;
  }

  .dagster-popover.bp5-dark .bp5-popover-arrow {
    z-index: 9;
    &:before {
      display: none;
    }
  }

  .dagster-popover.bp5-dark a {
    color: inherit;
  }

  .dagster-popover .bp5-popover.bp5-dark .bp5-popover-content,
  .bp5-dark .dagster-popover .bp5-popover .bp5-popover-content {
    background-color: ${Colors.tooltipBackground()};
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
