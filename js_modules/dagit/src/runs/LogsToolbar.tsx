import {Button, Checkbox, Colors, IconName, Tag} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ComputeLogLink} from 'src/runs/ComputeLogModal';
import {LogLevel} from 'src/runs/LogLevel';
import {LogFilter, LogFilterValue} from 'src/runs/LogsProvider';
import {IStepState, IRunMetadataDict} from 'src/runs/RunMetadataProvider';
import {getRunFilterProviders} from 'src/runs/getRunFilterProviders';
import {SuggestionProvider, TokenizingField, TokenizingFieldValue} from 'src/ui/TokenizingField';

interface ILogsToolbarProps {
  steps: string[];
  filter: LogFilter;
  metadata: IRunMetadataDict;

  onSetFilter: (filter: LogFilter) => void;
}

const suggestionProvidersFilter = (
  suggestionProviders: SuggestionProvider[],
  values: TokenizingFieldValue[],
) => {
  // This filters down autocompletion suggestion providers based on what you've already typed.
  // It allows us to remove all autocompletions for "step:" if values already contains a step.
  const usedTokens = values.map((v) => v.token).filter(Boolean);
  const singleUseTokens = ['step', 'type'];

  return suggestionProviders.filter(
    ({token}) => !singleUseTokens.includes(token) || !usedTokens.includes(token),
  );
};

export const LogsToolbar: React.FunctionComponent<ILogsToolbarProps> = (props) => {
  const {steps, filter, metadata, onSetFilter} = props;

  const [copyIcon, setCopyIcon] = React.useState<IconName>(IconNames.CLIPBOARD);
  const selectedStep = filter.logQuery.find((v) => v.token === 'step')?.value || null;
  const selectedStepState =
    (selectedStep && metadata.steps[selectedStep]?.state) || IStepState.PREPARING;

  const filterText = filter.logQuery.reduce((accum, value) => accum + value.value, '');

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

  return (
    <LogsToolbarContainer>
      <TokenizingField
        small
        values={filter.logQuery}
        onChangeBeforeCommit
        onChange={(logQuery: LogFilterValue[]) => onSetFilter({...filter, logQuery})}
        suggestionProviders={getRunFilterProviders(steps)}
        suggestionProvidersFilter={suggestionProvidersFilter}
        loading={false}
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
      {selectedStep && (
        <ComputeLogLink stepKey={selectedStep} runState={selectedStepState}>
          View Raw Step Output
        </ComputeLogLink>
      )}
      <div style={{minWidth: 15, flex: 1}} />
      <div style={{marginRight: '8px'}}>
        <Button
          text="Copy URL"
          small={true}
          icon={copyIcon}
          onClick={() => {
            navigator.clipboard.writeText(window.location.href);
            setCopyIcon(IconNames.SAVED);
          }}
        />
      </div>
      <Button
        text={'Clear'}
        small={true}
        icon={IconNames.ERASER}
        onClick={() => onSetFilter({...filter, sinceTime: Date.now()})}
      />
    </LogsToolbarContainer>
  );
};

const LogsToolbarContainer = styled.div`
  display: flex;
  flex-direction: row;
  background: ${Colors.WHITE};
  align-items: center;
  padding: 5px 15px;
  border-bottom: 1px solid ${Colors.GRAY4};
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.07);
  z-index: 2;
`;

const NonMatchCheckbox = styled(Checkbox)`
  &&& {
    margin: 0 4px 0 12px;
  }
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
