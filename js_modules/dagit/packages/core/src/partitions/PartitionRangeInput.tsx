import {Icon, TextInput} from '@dagster-io/ui';
import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {ClearButton} from '../ui/ClearButton';

export const PartitionRangeInput: React.FC<{
  value: string[];
  onChange: (partitionNames: string[]) => void;
  partitionKeys: string[];
  isTimeseries: boolean;
}> = ({value, onChange, partitionKeys, isTimeseries}) => {
  const [valueString, setValueString] = React.useState('');
  const partitionNameJSON = React.useMemo(() => JSON.stringify(partitionKeys), [partitionKeys]);

  React.useEffect(() => {
    const partitionNameArr = JSON.parse(partitionNameJSON);
    setValueString(isTimeseries ? partitionsToText(value, partitionNameArr) : value.join(', '));
  }, [value, partitionNameJSON, isTimeseries]);

  const placeholder = React.useMemo(() => {
    return placeholderForPartitions(partitionKeys, isTimeseries);
  }, [partitionKeys, isTimeseries]);

  const tryCommit = (e: React.SyntheticEvent<HTMLInputElement>) => {
    try {
      onChange(textToPartitions(valueString, partitionKeys));
    } catch (err: any) {
      e.preventDefault();
      showCustomAlert({body: err.message});
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      tryCommit(e);
    }
  };

  return (
    <TextInput
      placeholder={placeholder}
      value={valueString}
      style={{display: 'flex', width: '100%', flex: 1, flexGrow: 1}}
      onChange={(e) => setValueString(e.currentTarget.value)}
      onKeyDown={onKeyDown}
      onBlur={tryCommit}
      rightElement={
        <ClearButton
          style={{display: valueString.length ? 'initial' : 'none'}}
          onClick={() => onChange([])}
        >
          <Icon name="cancel" />
        </ClearButton>
      }
    />
  );
};

export function assembleIntoSpans<T>(keys: string[], keyTestFn: (key: string, idx: number) => T) {
  const spans: {startIdx: number; endIdx: number; status: T}[] = [];

  for (let ii = 0; ii < keys.length; ii++) {
    const status = keyTestFn(keys[ii], ii);
    if (!spans.length || spans[spans.length - 1].status !== status) {
      spans.push({startIdx: ii, endIdx: ii, status});
    } else {
      spans[spans.length - 1].endIdx = ii;
    }
  }

  return spans;
}

export function stringForSpan(
  {startIdx, endIdx}: {startIdx: number; endIdx: number},
  all: string[],
) {
  return startIdx === endIdx ? all[startIdx] : `[${all[startIdx]}...${all[endIdx]}]`;
}

function placeholderForPartitions(names: string[], isTimeseries: boolean) {
  if (names.length === 0) {
    return '';
  }
  if (names.length < 4 || !isTimeseries) {
    return `ex: ${names[0]}, ${names[1]}`;
  }
  return `ex: ${names[0]}, ${names[1]}, [${names[2]}...${names[names.length - 1]}]`;
}

function textToPartitions(selected: string, all: string[]) {
  const terms = selected.split(',').map((s) => s.trim());
  const result = [];
  for (const term of terms) {
    if (term.length === 0) {
      continue;
    }
    const rangeMatch = /^\[(.*)\.\.\.(.*)\]$/g.exec(term);
    if (rangeMatch) {
      const [, start, end] = rangeMatch;
      const allStartIdx = all.indexOf(start);
      const allEndIdx = all.indexOf(end);
      if (allStartIdx === -1 || allEndIdx === -1) {
        throw new Error(`Could not find partitions for provided range: ${start}...${end}`);
      }
      result.push(...all.slice(allStartIdx, allEndIdx + 1));
    } else if (term.includes('*')) {
      const [prefix, suffix] = term.split('*');
      result.push(...all.filter((p) => p.startsWith(prefix) && p.endsWith(suffix)));
    } else {
      const idx = all.indexOf(term);
      if (idx === -1) {
        throw new Error(`Could not find partition: ${term}`);
      }
      result.push(term);
    }
  }
  return result.sort((a, b) => all.indexOf(a) - all.indexOf(b));
}

function partitionsToText(selected: string[], all: string[]) {
  return assembleIntoSpans(all, (key) => selected.includes(key))
    .filter((s) => s.status)
    .map((s) => stringForSpan(s, all))
    .join(', ');
}
