import {Menu, MenuItem} from '@dagster-io/ui-components';
import {MutableRefObject} from 'react';

import {Suggestion} from './SelectionAutoCompleteVisitor';
import {IndeterminateLoadingBar} from '../ui/IndeterminateLoadingBar';

type SelectionInputAutoCompleteResultsProps = {
  results: {
    list: Suggestion[];
    from: number;
    to: number;
  } | null;
  width?: number;
  onSelect: (suggestion: Suggestion) => void;
  selectedIndex: number;
  setSelectedIndex: React.Dispatch<React.SetStateAction<{current: number}>>;
  scrollToSelection: MutableRefObject<boolean>;
  loading?: boolean;
};

export const SelectionInputAutoCompleteResults = ({
  results,
  width,
  onSelect,
  selectedIndex,
  setSelectedIndex,
  scrollToSelection,
  loading,
}: SelectionInputAutoCompleteResultsProps) => {
  if (!results && !loading) {
    return null;
  }

  return (
    <div style={{width}}>
      <Menu style={{maxHeight: '300px', overflowY: 'auto'}}>
        {results?.list.map((result, index) => (
          <MenuItem
            key={result.text}
            text={
              <div
                ref={
                  index === selectedIndex && scrollToSelection.current
                    ? (el) => {
                        scrollToSelection.current = false;
                        if (el) {
                          el.scrollIntoView({
                            behavior: 'instant',
                            block: 'center',
                          });
                        }
                      }
                    : null
                }
              >
                {result.displayText}
              </div>
            }
            active={index === selectedIndex}
            onClick={() => onSelect(result)}
            onMouseEnter={() => setSelectedIndex({current: index})}
          />
        ))}
      </Menu>
      <IndeterminateLoadingBar $loading={loading} />
    </div>
  );
};
