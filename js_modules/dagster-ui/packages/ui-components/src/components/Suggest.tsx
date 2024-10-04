// eslint-disable-next-line no-restricted-imports
import {InputGroupProps, PopoverProps} from '@blueprintjs/core';
// eslint-disable-next-line no-restricted-imports
import {
  Suggest as BlueprintSuggest,
  ItemListRendererProps,
  SuggestProps,
  isCreateNewItem,
} from '@blueprintjs/select';
import {useVirtualizer} from '@tanstack/react-virtual';
import deepmerge from 'deepmerge';
import * as React from 'react';
import styled, {createGlobalStyle} from 'styled-components';

import {Box} from './Box';
import {Colors} from './Color';
import {Icon, IconName, IconWrapper} from './Icon';
import {TextInputContainerStyles, TextInputStyles} from './TextInput';
import {Container, Inner, Row} from './VirtualizedTable';

export const GlobalSuggestStyle = createGlobalStyle`
  .dagster-suggest-input.bp5-input-group {
    ${TextInputContainerStyles}

    &:disabled ${IconWrapper}:first-child {
      background-color: ${Colors.accentGray()};
    }

    .bp5-input {
      ${TextInputStyles}

      height: auto;

      ::placeholder {
        color: ${Colors.textDisabled()};
      }
    }

    .bp5-input-action {
      height: auto;
      top: 1px;
      right: 2px;
    }
  }


  .bp5-select-popover.dagster-popover,
  .bp5-suggest-popover.dagster-popover {
    .bp5-popover-content li {
      list-style: none;
      margin: 0;
      padding: 0;
    }
  }
`;

export const MENU_ITEM_HEIGHT = 32;

// arbitrary, just looks nice
const MAX_MENU_HEIGHT = 240;
const MENU_WIDTH = 250;

interface Props<T> extends React.PropsWithChildren<SuggestProps<T>> {
  itemHeight?: number;
  menuWidth?: number;
  icon?: IconName;
}

export const Suggest = <T,>(props: Props<T>) => {
  const {popoverProps = {}, menuWidth = MENU_WIDTH, noResults, icon, ...rest} = props;

  const allPopoverProps: Partial<PopoverProps> = {
    ...popoverProps,
    minimal: true,
    modifiers: deepmerge({offset: {enabled: true, offset: '0, 8px'}}, popoverProps.modifiers || {}),
    popoverClassName: `dagster-popover ${props.popoverProps?.className || ''}`,
  };

  const inputProps: Partial<InputGroupProps> = {
    ...props.inputProps,
    className: 'dagster-suggest-input',
  };

  const suggest = (
    <BlueprintSuggest<T>
      {...rest}
      inputProps={inputProps}
      popoverProps={allPopoverProps}
      itemListRenderer={(props) => {
        const {filteredItems} = props;
        if (filteredItems.length === 0 && noResults) {
          return (
            <Box
              padding={{vertical: 4, horizontal: 8}}
              style={{width: menuWidth, outline: 'none', cursor: 'default'}}
            >
              {noResults}
            </Box>
          );
        }

        return <SuggestionList {...props} menuWidth={menuWidth} />;
      }}
    />
  );

  if (icon) {
    return (
      <SuggestWithIconWrapper>
        <div>
          <Icon name={icon} />
        </div>
        {suggest}
      </SuggestWithIconWrapper>
    );
  }
  return suggest;
};

interface SuggestionListProps<T> extends ItemListRendererProps<T> {
  menuWidth?: number;
}

const SuggestionList = <T,>(props: SuggestionListProps<T>) => {
  const {filteredItems, activeItem, menuWidth = MENU_WIDTH} = props;

  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const rowVirtualizer = useVirtualizer({
    count: filteredItems.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (_) => 32,
    overscan: 10,
  });

  const items = rowVirtualizer.getVirtualItems();
  const totalHeight = rowVirtualizer.getTotalSize();
  const activeIndex =
    activeItem && !isCreateNewItem(activeItem) ? filteredItems.indexOf(activeItem) : -1;

  React.useEffect(() => {
    if (activeIndex !== -1) {
      rowVirtualizer.scrollToIndex(activeIndex);
    }
  }, [rowVirtualizer, activeIndex]);

  return (
    <div style={{overflow: 'hidden'}}>
      <Container ref={parentRef} style={{maxHeight: MAX_MENU_HEIGHT, width: menuWidth}}>
        <Inner $totalHeight={totalHeight}>
          {items.map(({index, key, size, start}) => {
            const item = filteredItems[index]!;
            return (
              <Row key={key} $height={size} $start={start}>
                {props.renderItem(item, index)}
              </Row>
            );
          })}
        </Inner>
      </Container>
    </div>
  );
};

const SuggestWithIconWrapper = styled.div`
  position: relative;
  > :first-child {
    position: absolute;
    left: 8px;
    z-index: 1;
    top: 0;
    bottom: 0;
    display: flex;
    align-items: center;
  }

  &&& input {
    padding-left: 28px;
  }
`;
