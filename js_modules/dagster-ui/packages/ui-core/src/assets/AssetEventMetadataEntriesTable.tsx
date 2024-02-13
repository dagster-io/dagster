import {Box, Caption, Colors, Icon, Mono, Tag, TextInput} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import uniqBy from 'lodash/uniqBy';
import {useState} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {
  AssetMaterializationFragment,
  AssetObservationFragment,
} from './types/useRecentAssetEvents.types';
import {Timestamp} from '../app/time/Timestamp';
import {MetadataEntry} from '../metadata/MetadataEntry';
import {isTableSchemaEntry} from '../metadata/TableSchema';
import {MetadataEntryFragment} from '../metadata/types/MetadataEntry.types';
import {titleForRun} from '../runs/RunUtils';

type TableEvent = Pick<
  AssetObservationFragment | AssetMaterializationFragment,
  'metadataEntries'
> & {
  timestamp?: string | number;
  runId?: string;
};

/**
 * This component shows the metadata entries attached to an Asset Materialization or Observation event.
 * AssetNodes also have definition-time metadata, which is unrelated to this event metadata.
 */
export const AssetEventMetadataEntriesTable = ({
  event,
  observations,
  definitionMetadata,
  definitionLoadTimestamp,
  showDescriptions,
  showTimestamps,
  showHeader,
  showFilter,
  hideTableSchema,
}: {
  event: TableEvent | null;
  observations?: TableEvent[] | null;
  definitionMetadata?: MetadataEntryFragment[];
  definitionLoadTimestamp?: number;
  showDescriptions?: boolean;
  showTimestamps?: boolean;
  showHeader?: boolean;
  showFilter?: boolean;
  hideTableSchema?: boolean;
}) => {
  const [filter, setFilter] = useState('');

  const eventRows = event
    ? event.metadataEntries.map((entry) => ({
        icon: 'materialization' as const,
        timestamp: event.timestamp,
        runId: null,
        entry,
      }))
    : [];

  const observationRows = (observations || []).flatMap((o) =>
    o.metadataEntries.map((entry) => ({
      icon: 'observation' as const,
      timestamp: o.timestamp,
      runId: o.runId,
      entry,
    })),
  );

  const definitionRows = (definitionMetadata || []).map((entry) => ({
    icon: 'asset' as const,
    timestamp: definitionLoadTimestamp,
    runId: null,
    entry,
  }));

  // If there are multiple observation events that contain entries with the same label,
  // or if a metadata key is present on the definition and then emitted in an event,
  // only show the latest version (first one found)
  const allRows = uniqBy(
    [...observationRows, ...eventRows, ...definitionRows]
      .filter((row) => !filter || row.entry.label.toLowerCase().includes(filter.toLowerCase()))
      .filter((row) => !(hideTableSchema && isTableSchemaEntry(row.entry))),
    (e) => e.entry.label,
  );

  return (
    <>
      {showFilter && (
        <Box padding={{bottom: 12}}>
          <TextInput
            value={filter}
            style={{minWidth: 250}}
            icon="search"
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter metadata keys"
          />
        </Box>
      )}
      <AssetEventMetadataScrollContainer>
        <StyledTableWithHeader>
          {showHeader && (
            <thead>
              <tr>
                <td>Key</td>
                {showTimestamps && <td style={{width: 200}}>Timestamp</td>}
                <td>Value</td>
                {showDescriptions && <td>Description</td>}
              </tr>
            </thead>
          )}
          <tbody>
            {allRows.length === 0 && (
              <tr>
                <td colSpan={4}>
                  <Caption color={Colors.textLight()}>No metadata entries</Caption>
                </td>
              </tr>
            )}
            {allRows.map(({entry, timestamp, runId, icon}) => (
              <tr key={`metadata-${timestamp}-${entry.label}`}>
                <td>
                  <Mono>{entry.label}</Mono>
                </td>
                {showTimestamps && (
                  <td>
                    <Tag>
                      <Box flex={{gap: 4, alignItems: 'center'}}>
                        <Icon name={icon} />
                        <Timestamp timestamp={{ms: Number(timestamp)}} />
                      </Box>
                    </Tag>
                  </td>
                )}
                <td>
                  <Mono>
                    <MetadataEntry entry={entry} expandSmallValues={true} />
                  </Mono>
                </td>
                {showDescriptions && (
                  <td style={{opacity: 0.7}}>
                    {runId && (
                      <ObservedInRun
                        runId={runId}
                        timestamp={timestamp}
                        relativeTo={event?.timestamp}
                      />
                    )}
                    {entry.description}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </StyledTableWithHeader>
      </AssetEventMetadataScrollContainer>
    </>
  );
};

const ObservedInRun = ({
  runId,
  timestamp,
  relativeTo,
}: {
  runId: string;
  timestamp?: string | number;
  relativeTo?: string | number;
}) => (
  <>
    <Box>
      {`Observed in run `}
      <Link to={`/runs/${runId}?timestamp=${timestamp}`}>
        <Mono>{titleForRun({id: runId})}</Mono>
      </Link>
    </Box>
    <Caption>
      {`(${dayjs(Number(timestamp)).from(Number(relativeTo), true /* withoutSuffix */)} later)`}
    </Caption>
  </>
);

const AssetEventMetadataScrollContainer = styled.div`
  width: 100%;
  overflow-x: auto;
`;

export const StyledTableWithHeader = styled.table`
  width: 100%;
  border-spacing: 0;
  border-collapse: collapse;

  thead tr td {
    color: ${Colors.textLighter()};
    font-size: 12px;
    line-height: 16px;
  }

  tr td:first-child {
    max-width: 300px;
    word-wrap: break-word;
    width: 25%;
  }
  tr td {
    border: 1px solid ${Colors.keylineDefault()};
    padding: 8px 12px;
    font-size: 14px;
    line-height: 20px;
    vertical-align: top;
  }
`;
