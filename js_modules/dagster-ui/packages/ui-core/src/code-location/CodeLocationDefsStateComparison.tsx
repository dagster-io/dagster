import {Box, Colors, FontFamily, Icon, Table, Tag, Tooltip} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {DefsStateInfo, DefsStateManagementType} from '../graphql/types';
import {TimeFromNow} from '../ui/TimeFromNow';

interface Props {
  latestDefsStateInfo: DefsStateInfo | null;
  defsStateInfo: DefsStateInfo | null;
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
          latestManagementType: latestEntry?.info?.managementType || null,
          currentVersion: currentEntry?.info?.version || null,
          currentTimestamp: currentEntry?.info?.createTimestamp || null,
          currentManagementType: currentEntry?.info?.managementType || null,
        };
      })
      .sort((a, b) => (b.currentTimestamp || 0) - (a.currentTimestamp || 0));
  }, [latestDefsStateInfo, defsStateInfo]);

  const truncateVersion = (version: string | null) => {
    if (!version) {
      return '—';
    }
    return version.length > 8 ? version.substring(0, 8) : version;
  };

  const renderVersionCell = (
    version: string | null,
    managementType: DefsStateManagementType | null,
  ) => {
    if (!version || !managementType) {
      return '—';
    }

    // Render pills for special management types
    if (managementType === DefsStateManagementType.LOCAL_FILESYSTEM) {
      return (
        <Tooltip
          content="State is stored on the local filesystem or in the deployed image"
          placement="top"
        >
          <Tag>local filesystem</Tag>
        </Tooltip>
      );
    }

    if (managementType === DefsStateManagementType.LEGACY_CODE_SERVER_SNAPSHOTS) {
      return (
        <Tooltip content="State is stored in-memory on the code server" placement="top">
          <Tag>code server</Tag>
        </Tooltip>
      );
    }

    // Default: render the version hash for VERSIONED_STATE_STORAGE
    return (
      <Tooltip content={version} placement="top">
        <Tag>
          <span style={{fontFamily: FontFamily.monospace}}>{truncateVersion(version)}</span>
        </Tag>
      </Tooltip>
    );
  };

  const renderTimestampCell = (timestamp: number | null) => {
    if (!timestamp) {
      return '—';
    }

    return (
      <Tag>
        <TimeFromNow unixTimestamp={timestamp} />
      </Tag>
    );
  };

  const renderStatusCell = (
    latestVersion: string | null,
    currentVersion: string | null,
    currentManagementType: DefsStateManagementType | null,
    key: string,
  ) => {
    // For local filesystem and code server management types, always show "Up to date"
    if (
      currentManagementType === DefsStateManagementType.LOCAL_FILESYSTEM ||
      currentManagementType === DefsStateManagementType.LEGACY_CODE_SERVER_SNAPSHOTS
    ) {
      return (
        <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
          <Icon name="check_circle" color={Colors.accentGreen()} size={16} />
          <span style={{color: Colors.textGreen()}}>Up to date</span>
        </Box>
      );
    }

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
    <Table style={{width: '100%'}}>
      <thead>
        <tr>
          <th>Defs state key</th>
          <th>Current state</th>
          <th>Last updated</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {comparisonData.map(
          ({key, currentVersion, currentTimestamp, currentManagementType, latestVersion}) => (
            <tr key={key}>
              <td>{key}</td>
              <td>{renderVersionCell(currentVersion, currentManagementType)}</td>
              <td>{renderTimestampCell(currentTimestamp)}</td>
              <td>{renderStatusCell(latestVersion, currentVersion, currentManagementType, key)}</td>
            </tr>
          ),
        )}
      </tbody>
    </Table>
  );
};
