import {Button, Checkbox, Colors, IconName, Tag} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

import {LogLevel} from './LogLevel';
import {LogsFilterInput} from './LogsFilterInput';
import {LogFilter, LogFilterValue} from './LogsProvider';
import {IRunMetadataDict} from './RunMetadataProvider';
import {getRunFilterProviders} from './getRunFilterProviders';

interface ILogsToolbarProps {
  steps: string[];
  filter: LogFilter;
  metadata: IRunMetadataDict;

  onSetFilter: (filter: LogFilter) => void;
}

const logQueryToString = (logQuery: LogFilterValue[]) =>
  logQuery.map(({token, value}) => (token ? `${token}:${value}` : value)).join(' ');

export const LogsToolbar: React.FC<ILogsToolbarProps> = (props) => {
  const {steps, filter, onSetFilter} = props;
  const logQueryString = logQueryToString(filter.logQuery);

  const [queryString, setQueryString] = React.useState<string>(() => logQueryString);

  const [copyIcon, setCopyIcon] = React.useState<IconName>(IconNames.CLIPBOARD);
  const selectedStep = filter.logQuery.find((v) => v.token === 'step')?.value || null;

  const filterText = filter.logQuery.reduce((accum, value) => accum + value.value, '');

  // Reset the query string if the filter is updated, allowing external behavior
  // (e.g. clicking a Gantt step) to set the input.
  React.useEffect(() => {
    setQueryString(logQueryString);
  }, [logQueryString]);

  // Restore the clipboard icon after a delay.
  React.useEffect(() => {
    let token: any;
    if (copyIcon === IconNames.SAVED) {
      token = setTimeout(() => {
        setCopyIcon(IconNames.CLIPBOARD);
      }, 2000);
    }
    return () => {
      token && clearTimeout(token);
    };
  }, [copyIcon]);

  const onChange = (value: string) => {
    const tokens = value.split(/\s+/);
    const logQuery = tokens.map((item) => {
      const segments = item.split(':');
      if (segments.length > 1) {
        return {token: segments[0], value: segments[1]};
      }
      return {value: segments[0]};
    });
    onSetFilter({...filter, logQuery: logQuery as LogFilterValue[]});
    setQueryString(value);
  };

  return (
    <LogsToolbarContainer>
      <LogsFilterInput
        value={queryString}
        suggestionProviders={getRunFilterProviders(steps)}
        onChange={onChange}
      />
      {filterText ? (
        <NonMatchCheckbox
          inline
          checked={filter.hideNonMatches}
          onChange={(event) =>
            onSetFilter({...filter, hideNonMatches: event.currentTarget.checked})
          }
        >
          Hide non-matches
        </NonMatchCheckbox>
      ) : null}
      <LogsToolbarDivider />
      <div style={{display: 'flex'}}>
        {Object.keys(LogLevel).map((level) => {
          const enabled = filter.levels[level];
          return (
            <FilterTag
              key={level}
              intent={enabled ? 'primary' : 'none'}
              interactive
              minimal={!enabled}
              onClick={() =>
                onSetFilter({
                  ...filter,
                  levels: {
                    ...filter.levels,
                    [level]: !enabled,
                  },
                })
              }
              round
            >
              {level.toLowerCase()}
            </FilterTag>
          );
        })}
      </div>
      {selectedStep && <LogsToolbarDivider />}
      <div style={{minWidth: 15, flex: 1}} />
      <div style={{marginRight: '8px'}}>
        <Button
          small
          icon={copyIcon}
          onClick={() => {
            navigator.clipboard.writeText(window.location.href);
            setCopyIcon(IconNames.SAVED);
          }}
          text="Copy URL"
        />
      </div>
    </LogsToolbarContainer>
  );
};

const LogsToolbarContainer = styled.div`
  display: flex;
  flex-direction: row;
  background: ${Colors.WHITE};
  align-items: center;
  padding: 4px 8px;
  border-bottom: 1px solid ${Colors.GRAY4};
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.07);
  z-index: 2;
`;

const NonMatchCheckbox = styled(Checkbox)`
  &&& {
    margin: 0 4px 0 12px;
  }

  white-space: nowrap;
`;

const LogsToolbarDivider = styled.div`
  display: inline-block;
  width: 1px;
  height: 30px;
  margin: 0 8px;
  border-right: 1px solid ${Colors.LIGHT_GRAY3};
`;

const FilterTag = styled(Tag)`
  margin-right: 8px;
  text-transform: capitalize;
  opacity: ${({minimal}) => (minimal ? '0.5' : '1')};
`;
