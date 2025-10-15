import {Box, Colors, FontFamily, Icon, Table, Tag} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {TimeFromNow} from '../ui/TimeFromNow';
import {DefsStateInfoFragment} from './types/CodeLocationDefsStateQuery.types';

interface Props {
  latestDefsStateInfo: DefsStateInfoFragment | null;
  defsStateInfo: DefsStateInfoFragment | null;
}

export const CodeLocationDefsStateComparison = ({latestDefsStateInfo, defsStateInfo}: Props) => {
  const comparisonData = useMemo(() => {
    // Use the current defs state info as the primary source for table rows
    const currentKeys = new Set<string>();
    defsStateInfo?.keyStateInfo.forEach((entry) => {
      if (entry) {
        currentKeys.add(entry.name);
      }
    });

    // Build comparison data only for keys that exist in the current state
    return Array.from(currentKeys)
      .map((key) => {
        const latestEntry = latestDefsStateInfo?.keyStateInfo?.find((entry) => entry?.name === key);
        const currentEntry = defsStateInfo?.keyStateInfo?.find((entry) => entry?.name === key);

        return {
          key,
          latestVersion: latestEntry?.info?.version || null,
          latestTimestamp: latestEntry?.info?.createTimestamp || null,
          currentVersion: currentEntry?.info?.version || null,
          currentTimestamp: currentEntry?.info?.createTimestamp || null,
        };
      })
      .sort((a, b) => a.key.localeCompare(b.key));
  }, [latestDefsStateInfo, defsStateInfo]);

  const truncateVersion = (version: string | null) => {
    if (!version) {
      return '—';
    }
    return version.length > 8 ? version.substring(0, 8) : version;
  };

  const renderVersionCell = (version: string | null, timestamp: number | null) => {
    if (!version || !timestamp) {
      return '—';
    }

    return (
      <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
        <span style={{fontFamily: FontFamily.monospace}}>{truncateVersion(version)}</span>
        <Tag>
          <TimeFromNow unixTimestamp={timestamp} />
        </Tag>
      </Box>
    );
  };

  const renderStatusCell = (
    latestVersion: string | null,
    currentVersion: string | null,
    key: string,
  ) => {
    if (!latestVersion) {
      return (
        <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
          <Icon name="warning" color={Colors.accentYellow()} size={16} />
          <span style={{color: Colors.textYellow()}}>No state available</span>
        </Box>
      );
    } else if (latestVersion === currentVersion) {
      return (
        <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
          <Icon name="check_circle" color={Colors.accentGreen()} size={16} />
          <span style={{color: Colors.textGreen()}}>Up to date</span>
        </Box>
      );
    } else {
      const latestEntry = latestDefsStateInfo?.keyStateInfo?.find((e) => e?.name === key);
      return (
        <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
          <Icon name="warning" color={Colors.accentYellow()} size={16} />
          <span style={{color: Colors.textYellow()}}>Update available</span>
          <Tag>
            <TimeFromNow unixTimestamp={latestEntry?.info?.createTimestamp || 0} />
          </Tag>
        </Box>
      );
    }
  };

  return (
    <Box>
      <Table style={{width: '100%'}}>
        <thead>
          <tr>
            <th
              style={{
                textAlign: 'left',
                padding: '8px 12px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
                width: '25%',
              }}
            >
              Definition Key
            </th>
            <th
              style={{
                textAlign: 'left',
                padding: '8px 12px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
                width: '20%',
              }}
            >
              Current State
            </th>
            <th
              style={{
                textAlign: 'left',
                padding: '8px 12px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
                width: '55%',
              }}
            >
              Status
            </th>
          </tr>
        </thead>
        <tbody>
          {comparisonData.map(({key, currentVersion, currentTimestamp, latestVersion}) => (
            <tr key={key}>
              <td style={{padding: '8px 12px', fontFamily: FontFamily.monospace}}>{key}</td>
              <td style={{padding: '8px 12px'}}>
                {renderVersionCell(currentVersion, currentTimestamp)}
              </td>
              <td style={{padding: '8px 12px'}}>
                {renderStatusCell(latestVersion, currentVersion, key)}
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Box>
  );
};
