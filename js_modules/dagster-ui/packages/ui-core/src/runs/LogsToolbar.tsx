import {
  Box,
  Button,
  ButtonGroup,
  Checkbox,
  ExternalAnchorButton,
  Icon,
  IconName,
  MenuItem,
  Suggest,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {FilterOption, LogFilterSelect} from './LogFilterSelect';
import {LogLevel} from './LogLevel';
import {LogsFilterInput} from './LogsFilterInput';
import {LogFilter, LogFilterValue} from './LogsProvider';
import {IRunMetadataDict, extractLogCaptureStepsFromLegacySteps} from './RunMetadataProvider';
import {getRunFilterProviders} from './getRunFilterProviders';
import {EnabledRunLogLevelsKey, validateLogLevels} from './useQueryPersistedLogFilter';
import {OptionsContainer, OptionsDivider} from '../gantt/VizComponents';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

export enum LogType {
  structured = 'structured',
  stdout = 'stdout',
  stderr = 'stderr',
}

interface ILogsToolbarProps {
  steps: string[];
  metadata: IRunMetadataDict;
  counts: LogLevelCounts;

  filter: LogFilter;
  onSetFilter: (filter: LogFilter) => void;
  logType: LogType;
  onSetLogType: (logType: LogType) => void;
  computeLogFileKey?: string;
  onSetComputeLogKey: (key: string) => void;
  computeLogUrl: string | null;

  children?: React.ReactNode;
}

interface WithExpandCollapseProps extends ILogsToolbarProps {
  isSectionExpanded: boolean;
  toggleExpanded: () => void;
}

const logQueryToString = (logQuery: LogFilterValue[]) =>
  logQuery.map(({token, value}) => (token ? `${token}:${value}` : value)).join(' ');

export const LogsToolbar = (props: ILogsToolbarProps | WithExpandCollapseProps) => {
  const {
    steps,
    metadata,
    counts,
    filter,
    onSetFilter,
    logType,
    onSetLogType,
    computeLogFileKey,
    onSetComputeLogKey,
    computeLogUrl,
    children,
  } = props;
  let isSectionExpanded;
  let toggleExpanded;

  if ('isSectionExpanded' in props) {
    isSectionExpanded = props.isSectionExpanded;
    toggleExpanded = props.toggleExpanded;
  }

  const activeItems = React.useMemo(() => new Set([logType]), [logType]);

  return (
    <OptionsContainer style={{gap: 12}}>
      <ButtonGroup
        activeItems={activeItems}
        buttons={[
          {id: LogType.structured, icon: 'logs_structured', label: 'Events'},
          {id: LogType.stdout, icon: 'logs_stdout', label: 'stdout'},
          {id: LogType.stderr, icon: 'logs_stderr', label: 'stderr'},
        ]}
        onClick={(id) => onSetLogType(id)}
      />
      {logType === 'structured' ? (
        <StructuredLogToolbar
          counts={counts}
          filter={filter}
          onSetFilter={onSetFilter}
          steps={steps}
        />
      ) : (
        <ComputeLogToolbar
          steps={steps}
          metadata={metadata}
          computeLogFileKey={computeLogFileKey}
          onSetComputeLogKey={onSetComputeLogKey}
          computeLogUrl={computeLogUrl}
        />
      )}
      {children}
      {toggleExpanded ? (
        <Tooltip content={isSectionExpanded ? 'Collapse' : 'Expand'}>
          <Button
            icon={<Icon name={isSectionExpanded ? 'collapse_arrows' : 'expand_arrows'} />}
            onClick={toggleExpanded}
          />
        </Tooltip>
      ) : null}
    </OptionsContainer>
  );
};

export const ComputeLogToolbar = ({
  steps,
  metadata,
  computeLogFileKey,
  onSetComputeLogKey,
  computeLogUrl,
}: {
  metadata: IRunMetadataDict;
  steps?: string[];
  computeLogFileKey?: string;
  onSetComputeLogKey: (step: string) => void;
  computeLogUrl: string | null;
}) => {
  const logCaptureSteps =
    metadata.logCaptureSteps || extractLogCaptureStepsFromLegacySteps(Object.keys(metadata.steps));

  const logCaptureInfo = computeLogFileKey ? logCaptureSteps[computeLogFileKey] : undefined;
  const isValidStepSelection = !!logCaptureInfo;

  const fileKeyText = (fileKey?: string) => {
    if (!fileKey) {
      return '';
    }
    const captureInfo = logCaptureSteps[fileKey];
    if (!captureInfo) {
      return '';
    }

    if (
      captureInfo.stepKeys.length === 1 &&
      (captureInfo.pid || captureInfo.stepKeys[0] === fileKey)
    ) {
      return captureInfo.stepAttemptNumber
        ? `${captureInfo.stepKeys[0]} (Attempt #${captureInfo.stepAttemptNumber})`
        : `${captureInfo.stepKeys[0]}`;
    }

    if (captureInfo.pid) {
      return `pid: ${captureInfo.pid} (${captureInfo.stepKeys.length} steps)`;
    }
    return `${fileKey} (${captureInfo.stepKeys.length} steps)`;
  };

  return (
    <Box
      flex={{justifyContent: 'space-between', alignItems: 'center', direction: 'row'}}
      style={{flex: 1}}
    >
      <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
        {steps ? (
          <div style={{width: 200}}>
            <Suggest
              resetOnClose
              inputProps={{placeholder: 'Select a step…'}}
              activeItem={computeLogFileKey}
              selectedItem={computeLogFileKey}
              disabled={!steps.length}
              items={Object.keys(logCaptureSteps)}
              noResults="No matching steps"
              inputValueRenderer={(item) => fileKeyText(item)}
              itemPredicate={(query, item) =>
                fileKeyText(item).toLocaleLowerCase().includes(query.toLocaleLowerCase())
              }
              itemRenderer={(item, itemProps) => (
                <MenuItem
                  active={itemProps.modifiers.active}
                  onClick={(e) => itemProps.handleClick(e)}
                  text={fileKeyText(item)}
                  key={item}
                />
              )}
              onItemSelect={(fileKey) => {
                onSetComputeLogKey(fileKey);
              }}
            />
          </div>
        ) : undefined}

        {!steps ? <Box>Step: {(logCaptureInfo?.stepKeys || []).join(', ')}</Box> : undefined}
      </Box>
      {isValidStepSelection ? (
        <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
          {computeLogUrl ? (
            <Tooltip
              placement="top-end"
              content={
                logCaptureInfo?.stepKeys.length === 1
                  ? `Download ${logCaptureInfo?.stepKeys[0]} compute logs`
                  : `Download compute logs`
              }
            >
              <ExternalAnchorButton
                icon={<Icon name="download_for_offline" />}
                aria-label="Download link"
                href={computeLogUrl}
                download
              >
                Download
              </ExternalAnchorButton>
            </Tooltip>
          ) : null}
        </Box>
      ) : null}
    </Box>
  );
};

export type LogLevelCounts = Record<LogLevel, number>;

const StructuredLogToolbar = ({
  filter,
  counts,
  onSetFilter,
  steps,
}: {
  filter: LogFilter;
  counts: LogLevelCounts;
  onSetFilter: (filter: LogFilter) => void;
  steps: string[];
}) => {
  const [copyIcon, setCopyIcon] = React.useState<IconName>('copy_to_clipboard');
  const logQueryString = logQueryToString(filter.logQuery);
  const [queryString, setQueryString] = React.useState<string>(() => logQueryString);

  // Persist the user's selected log level filters as defaults. We only _set_ the value here,
  // when the filter select changes -- the default is read from localStorage by
  // useQueryPersistedLogFilter.
  const [_, setStoredLogLevels] = useStateWithStorage(EnabledRunLogLevelsKey, validateLogLevels);

  const selectedStep = filter.logQuery.find((v) => v.token === 'step')?.value || null;
  const filterText = filter.logQuery.reduce((accum, value) => accum + value.value, '');

  // Reset the query string if the filter is updated, allowing external behavior
  // (e.g. clicking a Gantt step) to set the input.
  React.useEffect(() => {
    setQueryString(logQueryString);
  }, [logQueryString]);

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

  const onChangeFilter = React.useCallback(
    (level: LogLevel, enabled: boolean) => {
      const allEnabledFilters = new Set(
        Object.keys(filter.levels).filter((level) => !!filter.levels[level]),
      );

      // When changing log level filters, update localStorage with the selected levels
      // so that it persists as the default.
      enabled ? allEnabledFilters.add(level) : allEnabledFilters.delete(level);
      setStoredLogLevels(Array.from(allEnabledFilters));

      // Then, update the querystring.
      onSetFilter({
        ...filter,
        levels: {
          ...filter.levels,
          [level]: enabled,
        },
      });
    },
    [filter, onSetFilter, setStoredLogLevels],
  );

  // Restore the clipboard icon after a delay.
  React.useEffect(() => {
    let token: any;
    if (copyIcon === 'copy_to_clipboard_done') {
      token = setTimeout(() => {
        setCopyIcon('copy_to_clipboard');
      }, 2000);
    }
    return () => {
      token && clearTimeout(token);
    };
  }, [copyIcon]);

  const filterOptions = Object.fromEntries(
    Object.keys(LogLevel).map((level) => {
      return [
        level,
        {
          label: level.toLowerCase(),
          count: counts[level as LogLevel],
          enabled: !!filter.levels[level],
        },
      ] as [LogLevel, FilterOption];
    }),
  );

  return (
    <>
      <LogsFilterInput
        value={queryString}
        suggestionProviders={getRunFilterProviders(steps)}
        onChange={onChange}
      />
      {filterText ? (
        <NonMatchCheckbox
          checked={filter.hideNonMatches}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            onSetFilter({...filter, hideNonMatches: event.currentTarget.checked})
          }
          label="Hide non-matches"
        />
      ) : null}
      <Box flex={{direction: 'row', alignItems: 'center', gap: 8}} margin={{left: 12}}>
        <LogFilterSelect
          options={filterOptions as Record<LogLevel, FilterOption>}
          onSetFilter={onChangeFilter}
        />
      </Box>
      {selectedStep && <OptionsDivider />}
      <div style={{minWidth: 15, flex: 1}} />
    </>
  );
};

const NonMatchCheckbox = styled(Checkbox)`
  &&& {
    margin: 0 4px 0 12px;
  }

  white-space: nowrap;
`;
