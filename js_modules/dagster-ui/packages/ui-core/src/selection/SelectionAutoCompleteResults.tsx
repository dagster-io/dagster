import {Menu, MenuItem} from '@dagster-io/ui-components';
import {MutableRefObject} from 'react';

import {Suggestion} from './SelectionAutoComplete';

type SelectionAutoCompleteResultsProps = {
  results: {
    list: Suggestion[];
    from: number;
    to: number;
  } | null;
  width?: number;
  onSelect: (suggestion: Suggestion) => void;
  selectedIndex: number;
  setSelectedIndex: React.Dispatch<React.SetStateAction<{current: number}>>;
  scheduleUpdateValue: () => void;
  scrollToSelection: MutableRefObject<boolean>;
};

export const SelectionAutoCompleteResults = ({
  results,
  width,
  onSelect,
  selectedIndex,
  scheduleUpdateValue,
  setSelectedIndex,
  scrollToSelection,
}: SelectionAutoCompleteResultsProps) => {
  if (!results) {
    return null;
  }

  return (
    <div style={{width}}>
      {/* Call scheduleUpdateValue on scroll to reschedule the updateValue timeout */}
      <Menu style={{maxHeight: '300px', overflowY: 'auto'}} onScroll={scheduleUpdateValue}>
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
    </div>
  );
};
