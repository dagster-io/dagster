import {Tag, Tooltip} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {makeSensorKey} from '../sensors/makeSensorKey';
import {Container, Inner} from '../ui/VirtualizedTable';
import {findDuplicateRepoNames} from '../ui/findDuplicateRepoNames';
import {useRepoExpansionState} from '../ui/useRepoExpansionState';
import {VirtualizedSensorHeader, VirtualizedSensorRow} from '../workspace/VirtualizedSensorRow';
import {RepoRow} from '../workspace/VirtualizedWorkspaceTable';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

import {OVERVIEW_COLLAPSED_KEY} from './OverviewExpansionKey';
import {BasicInstigationStateFragment} from './types/BasicInstigationStateFragment.types';

type SensorInfo = {name: string; sensorState: BasicInstigationStateFragment};

type Repository = {
  repoAddress: RepoAddress;
  sensors: SensorInfo[];
};

interface Props {
  repos: Repository[];
  headerCheckbox: React.ReactNode;
  checkedKeys: Set<string>;
  onToggleCheckFactory: (path: string) => (values: {checked: boolean; shiftKey: boolean}) => void;
}

type RowType =
  | {type: 'header'; repoAddress: RepoAddress; sensorCount: number}
  | {type: 'sensor'; repoAddress: RepoAddress; sensor: SensorInfo};

export const OverviewSensorTable = ({
  repos,
  headerCheckbox,
  checkedKeys,
  onToggleCheckFactory,
}: Props) => {
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
    repos.forEach(({repoAddress, sensors}) => {
      flat.push({type: 'header', repoAddress, sensorCount: sensors.length});
      const repoKey = repoAddressAsHumanString(repoAddress);
      if (expandedKeys.includes(repoKey)) {
        sensors.forEach((sensor) => {
          flat.push({type: 'sensor', repoAddress, sensor});
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
      return row?.type === 'header' ? 32 : 64;
    },
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <>
      <VirtualizedSensorHeader checkbox={headerCheckbox} />
      <div style={{overflow: 'hidden'}}>
        <Container ref={parentRef}>
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, key, size, start}) => {
              const row: RowType = flattened[index];
              const type = row!.type;
              if (type === 'header') {
                return (
                  <RepoRow
                    repoAddress={row.repoAddress}
                    key={key}
                    height={size}
                    start={start}
                    onToggle={onToggle}
                    onToggleAll={onToggleAll}
                    expanded={expandedKeys.includes(repoAddressAsHumanString(row.repoAddress))}
                    showLocation={duplicateRepoNames.has(row.repoAddress.name)}
                    rightElement={
                      <Tooltip
                        content={row.sensorCount === 1 ? '1 sensor' : `${row.sensorCount} sensors`}
                        placement="top"
                      >
                        <Tag>{row.sensorCount}</Tag>
                      </Tooltip>
                    }
                  />
                );
              }

              const sensorKey = makeSensorKey(row.repoAddress, row.sensor.name);

              return (
                <VirtualizedSensorRow
                  key={key}
                  name={row.sensor.name}
                  sensorState={row.sensor.sensorState}
                  showCheckboxColumn={!!headerCheckbox}
                  checked={checkedKeys.has(sensorKey)}
                  onToggleChecked={onToggleCheckFactory(sensorKey)}
                  repoAddress={row.repoAddress}
                  height={size}
                  start={start}
                />
              );
            })}
          </Inner>
        </Container>
      </div>
    </>
  );
};
