import {InputGroupProps2, IPopoverProps} from '@blueprintjs/core';
// eslint-disable-next-line no-restricted-imports
import {Suggest as BlueprintSuggest, SuggestProps} from '@blueprintjs/select';
import deepmerge from 'deepmerge';
import * as React from 'react';
import {createGlobalStyle} from 'styled-components/macro';

import {ColorsWIP} from './Colors';

export const GlobalSuggestStyle = createGlobalStyle`
  .dagit-suggest-input.bp3-input-group {
    border: none;
    border-radius: 8px;

    align-items: center;
    display: inline-flex;
    flex-direction: row;
    flex-grow: 1;

    .bp3-input {
      border-radius: 8px;
      box-shadow: ${ColorsWIP.Gray300} inset 0px 0px 0px 1px,
        ${ColorsWIP.KeylineGray} inset 2px 2px 1.5px;
      height: auto;
      line-height: 20px;
      padding: 6px 6px 6px 12px;

      :disabled::placeholder {
        color: ${ColorsWIP.Gray400};
      }
    }

    /* Add more intents here as needed. */

    &.bp3-intent-danger .bp3-input {
      box-shadow: ${ColorsWIP.Red500} inset 0px 0px 0px 1px, ${ColorsWIP.KeylineGray} inset 2px 2px 1.5px;

      :focus {
        box-shadow: ${ColorsWIP.Red500} inset 0px 0px 0px 1px, ${ColorsWIP.KeylineGray} inset 2px 2px 1.5px, ${ColorsWIP.Red200} 0 0 0 3px;
      }
    }

    .bp3-input-action {
      height: auto;
      padding: 0;
      top: 1px;
      right: 2px;
    }
  }
`;

export const SuggestWIP = <T,>(props: React.PropsWithChildren<SuggestProps<T>>) => {
  const popoverProps: Partial<IPopoverProps> = {
    ...props.popoverProps,
    minimal: true,
    modifiers: deepmerge(
      {offset: {enabled: true, offset: '0, 8px'}},
      props.popoverProps?.modifiers || {},
    ),
    popoverClassName: `dagit-popover ${props.popoverProps?.className || ''}`,
  };

  const inputProps: Partial<InputGroupProps2> = {
    ...props.inputProps,
    className: 'dagit-suggest-input',
  };

  return <BlueprintSuggest {...props} inputProps={inputProps} popoverProps={popoverProps} />;
};
