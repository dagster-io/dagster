// eslint-disable-next-line no-restricted-imports
import {InputGroupProps2, IPopoverProps} from '@blueprintjs/core';
// eslint-disable-next-line no-restricted-imports
import {isCreateNewItem, Suggest as BlueprintSuggest, SuggestProps} from '@blueprintjs/select';
import deepmerge from 'deepmerge';
import * as React from 'react';
import {List} from 'react-virtualized';
import {createGlobalStyle} from 'styled-components/macro';

import {Colors} from './Colors';
import {IconWrapper} from './Icon';
import {TextInputContainerStyles, TextInputStyles} from './TextInput';

export const GlobalSuggestStyle = createGlobalStyle`
  .dagit-suggest-input.bp3-input-group {
    ${TextInputContainerStyles}

    &:disabled ${IconWrapper}:first-child {
      background-color: ${Colors.Gray400};
    }

    .bp3-input {
      ${TextInputStyles}

      height: auto;

      ::placeholder {
        color: ${Colors.Gray500};
      }
    }

    .bp3-input-action {
      height: auto;
      top: 1px;
      right: 2px;
    }
  }

  .bp3-select-popover.dagit-popover {
    .bp3-popover-content li {
      list-style: none;
      margin: 0;
      padding: 0;
    }
  }
`;

export const MENU_ITEM_HEIGHT = 32;

const MENU_WIDTH = 250; // arbitrary, just looks nice
const MENU_HEIGHT_MAX = MENU_ITEM_HEIGHT * 7.5;

export const Suggest = <T,>(props: React.PropsWithChildren<SuggestProps<T>>) => {
  const popoverProps: Partial<IPopoverProps> = {
    ...props.popoverProps,
    minimal: true,
    modifiers: deepmerge(
      {offset: {enabled: true, offset: '0 8px'}},
      props.popoverProps?.modifiers || {},
    ),
    popoverClassName: `dagit-popover ${props.popoverProps?.className || ''}`,
  };

  const inputProps: Partial<InputGroupProps2> = {
    ...props.inputProps,
    className: 'dagit-suggest-input',
  };

  return (
    <BlueprintSuggest<T>
      {...props}
      inputProps={inputProps}
      itemListRenderer={(props) => (
        <List
          style={{outline: 'none', marginRight: -5, paddingRight: 5}}
          rowCount={props.filteredItems.length}
          scrollToIndex={
            props.activeItem && !isCreateNewItem(props.activeItem)
              ? props.filteredItems.indexOf(props.activeItem)
              : undefined
          }
          rowHeight={MENU_ITEM_HEIGHT}
          rowRenderer={(a) => (
            <div key={a.index} style={a.style}>
              {props.renderItem(props.filteredItems[a.index] as T, a.index)}
            </div>
          )}
          width={MENU_WIDTH}
          height={Math.min(props.filteredItems.length * MENU_ITEM_HEIGHT, MENU_HEIGHT_MAX)}
        />
      )}
      popoverProps={popoverProps}
    />
  );
};
