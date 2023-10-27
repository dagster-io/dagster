import {MenuItem, useViewport, Suggest} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

export const SearchFilter = <T,>({
  values,
  onSelectValue,
}: {
  values: {label: string; value: T}[];
  onSelectValue: (e: React.MouseEvent<any>, value: T) => void;
}) => {
  const {viewport, containerProps} = useViewport();
  return (
    <SuggestWrapper {...containerProps}>
      <Suggest<(typeof values)[0]>
        key="asset-graph-explorer-search-bar"
        inputProps={{placeholder: 'Jump to…', style: {width: `min(100%, ${viewport.width}px)`}}}
        items={values}
        inputValueRenderer={(item) => item.label}
        itemPredicate={(query, item) =>
          item.label.toLocaleLowerCase().includes(query.toLocaleLowerCase())
        }
        menuWidth={viewport.width}
        popoverProps={{usePortal: false, fill: true}}
        itemRenderer={(item, itemProps) => (
          <MenuItem
            active={itemProps.modifiers.active}
            onClick={(e) => itemProps.handleClick(e)}
            key={item.label}
            text={item.label}
          />
        )}
        noResults={<MenuItem disabled={true} text="No results" />}
        onItemSelect={(item, e) => onSelectValue(e as any, item.value)}
        selectedItem={null}
      />
    </SuggestWrapper>
  );
};

const SuggestWrapper = styled.div`
  .bp4-input-group.dagster-suggest-input {
    width: 100%;
  }
`;
