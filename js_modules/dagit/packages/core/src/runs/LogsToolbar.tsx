import {
  Box,
  Button,
  ButtonGroup,
  Checkbox,
  Group,
  IconName,
  Icon,
  MenuItem,
  Select,
  Spinner,
  Tab,
  Tabs,
  IconWrapper,
  Colors,
  Tooltip,
} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {useCopyToClipboard} from '../app/browser';
import {OptionsContainer, OptionsDivider} from '../gantt/VizComponents';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

import {ExecutionStateDot} from './ExecutionStateDot';
import {FilterOption, LogFilterSelect} from './LogFilterSelect';
import {LogLevel} from './LogLevel';
import {LogsFilterInput} from './LogsFilterInput';
import {LogFilter, LogFilterValue} from './LogsProvider';
import {
  extractLogCaptureStepsFromLegacySteps,
  ILogCaptureInfo,
  IRunMetadataDict,
  IStepState,
} from './RunMetadataProvider';
import {getRunFilterProviders} from './getRunFilterProviders';
import {EnabledRunLogLevelsKey, validateLogLevels} from './useQueryPersistedLogFilter';

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
}

const logQueryToString = (logQuery: LogFilterValue[]) =>
  logQuery.map(({token, value}) => (token ? `${token}:${value}` : value)).join(' ');

const INITIAL_COMPUTE_LOG_TYPE = 'initial-compute-log-type';

export const LogsToolbar: React.FC<ILogsToolbarProps> = (props) => {
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
  } = props;

  const [
    initialComputeLogType,
    setInitialComputeLogType,
  ] = useStateWithStorage(INITIAL_COMPUTE_LOG_TYPE, (value: any) =>
    typeof value === 'string' ? (value as LogType) : LogType.stdout,
  );

  const activeItems = React.useMemo(
    () => new Set([logType === LogType.structured ? logType : LogType.stdout]),
    [logType],
  );

  const setComputeLogType = React.useCallback(
    (logType: LogType) => {
      setInitialComputeLogType(logType);
      onSetLogType(logType);
    },
    [onSetLogType, setInitialComputeLogType],
  );

  return (
    <OptionsContainer>
      <Box margin={{right: 12}}>
        <ButtonGroup
          activeItems={activeItems}
          buttons={[
            {id: LogType.structured, icon: 'list', tooltip: 'Structured event logs'},
            {id: initialComputeLogType, icon: 'wysiwyg', tooltip: 'Raw compute logs'},
          ]}
          onClick={(id) => onSetLogType(id)}
        />
      </Box>
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
          logType={logType}
          onSetLogType={setComputeLogType}
          computeLogFileKey={computeLogFileKey}
          onSetComputeLogKey={onSetComputeLogKey}
          computeLogUrl={computeLogUrl}
        />
      )}
    </OptionsContainer>
  );
};

const resolveState = (metadata: IRunMetadataDict, logCapture: ILogCaptureInfo) => {
  // resolves the state of potentially many steps into a single state so that we can show the
  // execution dot representing the status of this log capture group (potentially at the process
  // level)
  if (
    logCapture.stepKeys.some((stepKey) => metadata.steps[stepKey]!.state === IStepState.RUNNING)
  ) {
    return IStepState.RUNNING;
  }
  if (
    logCapture.stepKeys.some((stepKey) => metadata.steps[stepKey]!.state === IStepState.SKIPPED)
  ) {
    return IStepState.SKIPPED;
  }
  if (
    logCapture.stepKeys.every((stepKey) => metadata.steps[stepKey]!.state === IStepState.SUCCEEDED)
  ) {
    return IStepState.SUCCEEDED;
  }
  return IStepState.FAILED;
};

const ComputeLogToolbar = ({
  steps,
  metadata,
  computeLogFileKey,
  onSetComputeLogKey,
  logType,
  onSetLogType,
  computeLogUrl,
}: {
  steps: string[];
  metadata: IRunMetadataDict;
  computeLogFileKey?: string;
  onSetComputeLogKey: (step: string) => void;
  logType: LogType;
  onSetLogType: (type: LogType) => void;
  computeLogUrl: string | null;
}) => {
  const logCaptureSteps =
    metadata.logCaptureSteps || extractLogCaptureStepsFromLegacySteps(Object.keys(metadata.steps));
  const isValidStepSelection = computeLogFileKey && (logCaptureSteps as any)[computeLogFileKey];

  const fileKeyText = (fileKey?: string) => {
    if (!fileKey || !(logCaptureSteps as any)[fileKey]) {
      return null;
    }
    const captureInfo = (logCaptureSteps as any)[fileKey];
    if (captureInfo.stepKeys.length === 1 && fileKey === captureInfo.stepKeys[0]) {
      return fileKey;
    }
    if (captureInfo.pid && captureInfo.stepKeys.length === 1) {
      return captureInfo.stepKeys[0];
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
      <Group direction="row" spacing={24} alignItems="center">
        <Select
          disabled={!steps.length}
          items={Object.keys(logCaptureSteps)}
          itemPredicate={(query, item) =>
            item.toLocaleLowerCase().includes(query.toLocaleLowerCase())
          }
          itemRenderer={(item: string, options: {handleClick: any; modifiers: any}) => (
            <MenuItem
              key={item}
              onClick={options.handleClick}
              text={fileKeyText(item)}
              active={options.modifiers.active}
            />
          )}
          activeItem={computeLogFileKey}
          onItemSelect={(fileKey) => {
            onSetComputeLogKey(fileKey);
          }}
        >
          <Button disabled={!steps.length} rightIcon={<Icon name="expand_more" />}>
            {fileKeyText(computeLogFileKey) || 'Select a step...'}
          </Button>
        </Select>
        {isValidStepSelection ? (
          <Tabs selectedTabId={logType} onChange={onSetLogType} size="small">
            <Tab id={LogType.stdout} title="stdout" />
            <Tab id={LogType.stderr} title="stderr" />
          </Tabs>
        ) : null}
      </Group>
      {isValidStepSelection ? (
        <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
          {computeLogFileKey && (logCaptureSteps as any)[computeLogFileKey] ? (
            resolveState(metadata, (logCaptureSteps as any)[computeLogFileKey]) ===
            IStepState.RUNNING ? (
              <Spinner purpose="body-text" />
            ) : (
              <ExecutionStateDot
                state={resolveState(metadata, (logCaptureSteps as any)[computeLogFileKey])}
              />
            )
          ) : null}
          {computeLogUrl ? (
            <Tooltip
              placement="top-end"
              content={
                computeLogFileKey &&
                (logCaptureSteps as any)[computeLogFileKey]?.stepKeys.length === 1
                  ? `Download ${
                      (logCaptureSteps as any)[computeLogFileKey]?.stepKeys[0]
                    } compute logs`
                  : `Download compute logs`
              }
            >
              <DownloadLink aria-label="Download link" href={computeLogUrl} download>
                <Icon name="download_for_offline" color={Colors.Gray600} />
              </DownloadLink>
            </Tooltip>
          ) : null}
        </Box>
      ) : null}
    </Box>
  );
};

const DownloadLink = styled.a`
  border-radius: 4px;
  display: block;
  text-decoration: none;

  ${IconWrapper} {
    transition: background-color 100ms linear;
  }

  :hover ${IconWrapper} {
    background-color: ${Colors.Gray800};
  }

  :active ${IconWrapper}, :focus ${IconWrapper} {
    background-color: ${Colors.Dark};
  }

  :focus {
    outline: none;
  }
`;

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
  const [copyIcon, setCopyIcon] = React.useState<IconName>('assignment');
  const logQueryString = logQueryToString(filter.logQuery);
  const [queryString, setQueryString] = React.useState<string>(() => logQueryString);
  const copyToClipboard = useCopyToClipboard();

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
    if (copyIcon === 'assignment_turned_in') {
      token = setTimeout(() => {
        setCopyIcon('assignment');
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
      <Button
        icon={<Icon name={copyIcon} />}
        onClick={() => {
          copyToClipboard(window.location.href);
          setCopyIcon('assignment_turned_in');
        }}
      >
        Copy URL
      </Button>
    </>
  );
};

const NonMatchCheckbox = styled(Checkbox)`
  &&& {
    margin: 0 4px 0 12px;
  }

  white-space: nowrap;
`;
