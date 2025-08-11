import {Row} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {ObserveAutomationScheduleRow} from './ObserveAutomationScheduleRow';
import {ObserveAutomationSensorRow} from './ObserveAutomationSensorRow';
import {VirtualizedAutomationHeader} from './VirtualizedAutomationRow';
import {VirtualizedAutomationScheduleRow} from './VirtualizedAutomationScheduleRow';
import {VirtualizedAutomationSensorRow} from './VirtualizedAutomationSensorRow';
import {COMMON_COLLATOR} from '../app/Util';
import {useFeatureFlags} from '../app/useFeatureFlags';
import {OVERVIEW_COLLAPSED_KEY} from '../overview/OverviewExpansionKey';
import {makeAutomationKey} from '../sensors/makeSensorKey';
import {Container, Inner} from '../ui/VirtualizedTable';
import {findDuplicateRepoNames} from '../ui/findDuplicateRepoNames';
import {useRepoExpansionState} from '../ui/useRepoExpansionState';
import {DynamicRepoRow} from '../workspace/VirtualizedWorkspaceTable';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

type Repository = {
  repoAddress: RepoAddress;
  schedules: string[];
  sensors: string[];
};

interface Props {
  repos: Repository[];
  headerCheckbox: React.ReactNode;
  checkedKeys: Set<string>;
  onToggleCheckFactory: (path: string) => (values: {checked: boolean; shiftKey: boolean}) => void;
}

type RowType =
  | {type: 'header'; repoAddress: RepoAddress; scheduleCount: number; sensorCount: number}
  | {type: 'sensor'; repoAddress: RepoAddress; sensor: string}
  | {type: 'schedule'; repoAddress: RepoAddress; schedule: string};

export const AutomationsTable = ({
  repos,
  headerCheckbox,
  checkedKeys,
  onToggleCheckFactory,
}: Props) => {
  const {flagUseNewObserveUIs} = useFeatureFlags();
  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const allKeys = React.useMemo(
    () => repos.map(({repoAddress}) => repoAddressAsHumanString(repoAddress)),
    [repos],
  );
  const {expandedKeys, onToggle, onToggleAll} = useRepoExpansionState(
    OVERVIEW_COLLAPSED_KEY,
    allKeys,
  );

  const flattened: RowType[] = React.useMemo(() => {
    const flat: RowType[] = [];
    repos.forEach(({repoAddress, schedules, sensors}) => {
      flat.push({
        type: 'header',
        repoAddress,
        scheduleCount: schedules.length,
        sensorCount: sensors.length,
      });
      const repoKey = repoAddressAsHumanString(repoAddress);

      if (expandedKeys.includes(repoKey)) {
        const sensorKeys = new Set(sensors);
        const scheduleKeys = new Set(schedules);
        const repoAutomations = [...sensors, ...schedules].sort((a, b) =>
          COMMON_COLLATOR.compare(a, b),
        );

        repoAutomations.forEach((name) => {
          if (sensorKeys.has(name)) {
            flat.push({type: 'sensor', repoAddress, sensor: name});
          } else if (scheduleKeys.has(name)) {
            flat.push({type: 'schedule', repoAddress, schedule: name});
          }
        });
      }
    });
    return flat;
  }, [repos, expandedKeys]);

  const duplicateRepoNames = findDuplicateRepoNames(repos.map(({repoAddress}) => repoAddress.name));

  const rowVirtualizer = useVirtualizer({
    count: flattened.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (ii: number) => {
      const row = flattened[ii];
      return row?.type === 'header' ? 32 : 62;
    },
    overscan: 15,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <div style={{overflow: 'hidden'}}>
      <Container ref={parentRef}>
        {flagUseNewObserveUIs ? null : <VirtualizedAutomationHeader checkbox={headerCheckbox} />}
        <Inner $totalHeight={totalHeight}>
          {items.map(({index, key, size, start}) => {
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            const row: RowType = flattened[index]!;
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            const type = row!.type;
            if (type === 'header') {
              return (
                <Row $height={size} $start={start} key={key}>
                  <DynamicRepoRow
                    repoAddress={row.repoAddress}
                    ref={rowVirtualizer.measureElement}
                    index={index}
                    onToggle={onToggle}
                    onToggleAll={onToggleAll}
                    expanded={expandedKeys.includes(repoAddressAsHumanString(row.repoAddress))}
                    showLocation={duplicateRepoNames.has(row.repoAddress.name)}
                    rightElement={<></>}
                  />
                </Row>
              );
            }

            if (type === 'sensor') {
              const sensorKey = makeAutomationKey(row.repoAddress, row.sensor);
              if (flagUseNewObserveUIs) {
                return (
                  <Row $height={size} $start={start} key={key}>
                    <ObserveAutomationSensorRow
                      key={key}
                      index={index}
                      ref={rowVirtualizer.measureElement}
                      name={row.sensor}
                      checked={checkedKeys.has(sensorKey)}
                      onToggleChecked={onToggleCheckFactory(sensorKey)}
                      repoAddress={row.repoAddress}
                    />
                  </Row>
                );
              }

              return (
                <Row $height={size} $start={start} key={key}>
                  <VirtualizedAutomationSensorRow
                    index={index}
                    ref={rowVirtualizer.measureElement}
                    name={row.sensor}
                    checked={checkedKeys.has(sensorKey)}
                    onToggleChecked={onToggleCheckFactory(sensorKey)}
                    repoAddress={row.repoAddress}
                  />
                </Row>
              );
            }

            if (type === 'schedule') {
              const scheduleKey = makeAutomationKey(row.repoAddress, row.schedule);

              if (flagUseNewObserveUIs) {
                return (
                  <Row $height={size} $start={start} key={key}>
                    <ObserveAutomationScheduleRow
                      key={key}
                      index={index}
                      ref={rowVirtualizer.measureElement}
                      name={row.schedule}
                      checked={checkedKeys.has(scheduleKey)}
                      onToggleChecked={onToggleCheckFactory(scheduleKey)}
                      repoAddress={row.repoAddress}
                    />
                  </Row>
                );
              }

              return (
                <Row $height={size} $start={start} key={key}>
                  <VirtualizedAutomationScheduleRow
                    key={key}
                    index={index}
                    ref={rowVirtualizer.measureElement}
                    name={row.schedule}
                    checked={checkedKeys.has(scheduleKey)}
                    onToggleChecked={onToggleCheckFactory(scheduleKey)}
                    repoAddress={row.repoAddress}
                  />
                </Row>
              );
            }

            return <div key={key} />;
          })}
        </Inner>
      </Container>
    </div>
  );
};
