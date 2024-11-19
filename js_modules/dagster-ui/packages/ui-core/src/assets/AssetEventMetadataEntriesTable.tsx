import {
  Box,
  Button,
  ButtonGroup,
  Caption,
  Colors,
  Icon,
  Mono,
  Tag,
  TextInput,
  Tooltip,
} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import uniqBy from 'lodash/uniqBy';
import {useMemo, useState} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {AssetEventMetadataPlots} from './AssetEventMetadataPlots';
import {AssetKey} from './types';
import {
  AssetMaterializationFragment,
  AssetObservationFragment,
} from './types/useRecentAssetEvents.types';
import {Timestamp} from '../app/time/Timestamp';
import {
  HIDDEN_METADATA_ENTRY_LABELS,
  MetadataEntry,
  MetadataEntryLabelOnly,
  isCanonicalRowCountMetadataEntry,
} from '../metadata/MetadataEntry';
import {
  isCanonicalCodeSourceEntry,
  isCanonicalColumnLineageEntry,
  isCanonicalColumnSchemaEntry,
  isCanonicalTableNameEntry,
  isCanonicalUriEntry,
} from '../metadata/TableSchema';
import {MetadataEntryFragment} from '../metadata/types/MetadataEntryFragment.types';
import {titleForRun} from '../runs/RunUtils';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

type TableEvent = Pick<
  AssetObservationFragment | AssetMaterializationFragment,
  'metadataEntries'
> & {
  timestamp?: string | number;
  runId?: string;
};

interface Props {
  assetKey?: AssetKey;
  repoAddress: RepoAddress | null;
  event: TableEvent | null;
  observations?: TableEvent[] | null;
  definitionMetadata?: MetadataEntryFragment[];
  definitionLoadTimestamp?: number;
  assetHasDefinedPartitions?: boolean;
  showDescriptions?: boolean;
  showTimestamps?: boolean;
  showHeader?: boolean;
  showFilter?: boolean;
  hideEntriesShownOnOverview?: boolean;
  displayedByDefault?: number;
  emptyState?: React.ReactNode;
}

/**
 * This component shows the metadata entries attached to an Asset Materialization or Observation event.
 * AssetNodes also have definition-time metadata, which is unrelated to this event metadata.
 */
export const AssetEventMetadataEntriesTable = ({
  assetKey,
  event,
  observations,
  definitionMetadata,
  definitionLoadTimestamp,
  assetHasDefinedPartitions,
  showDescriptions,
  showTimestamps,
  showHeader,
  showFilter,
  hideEntriesShownOnOverview,
  displayedByDefault = 100,
  emptyState,
  repoAddress,
}: Props) => {
  const [filter, setFilter] = useState('');
  const [displayedCount, setDisplayedCount] = useState(displayedByDefault);
  const [view, setView] = useState<'table' | 'plots'>('table');
  const [plotView, setPlotView] = useState<'partition' | 'time'>(
    assetHasDefinedPartitions ? 'partition' : 'time',
  );

  // If there are multiple observation events that contain entries with the same label,
  // or if a metadata key is present on the definition and then emitted in an event,
  // only show the latest version (first one found)
  const allRows = useMemo(() => {
    const eventRows = event
      ? event.metadataEntries.map((entry) => ({
          tooltip: `Materialized ${dayjs(Number(event.timestamp)).fromNow()}${
            event.runId ? ` in run ${event.runId?.slice(0, 8)}` : ``
          }`,
          icon: 'materialization' as const,
          timestamp: event.timestamp,
          runId: null,
          entry,
        }))
      : [];

    const observationRows = (observations || []).flatMap((o) =>
      o.metadataEntries.map((entry) => ({
        tooltip: `Observed ${dayjs(Number(o.timestamp)).fromNow()}${
          o.runId ? ` in run ${o.runId.slice(0, 8)}` : ``
        }`,
        icon: 'observation' as const,
        timestamp: o.timestamp,
        runId: o.runId,
        entry,
      })),
    );

    const definitionRows = (definitionMetadata || []).map((entry) => ({
      tooltip: `Loaded ${dayjs(definitionLoadTimestamp).fromNow()}${
        repoAddress ? ` from ${repoAddressAsHumanString(repoAddress)}` : ''
      }`,
      icon: 'asset' as const,
      timestamp: definitionLoadTimestamp,
      runId: null,
      entry,
    }));

    return uniqBy([...observationRows, ...eventRows, ...definitionRows], (e) => e.entry.label);
  }, [definitionLoadTimestamp, definitionMetadata, event, observations, repoAddress]);

  const filteredRows = useMemo(
    () =>
      allRows
        .filter((row) => !filter || row.entry.label.toLowerCase().includes(filter.toLowerCase()))
        .filter((row) => !isEntryHidden(row.entry, {hideEntriesShownOnOverview})),
    [allRows, filter, hideEntriesShownOnOverview],
  );

  if (emptyState && allRows.length === 0) {
    return emptyState;
  }

  return (
    <>
      {showFilter && (
        <Box
          padding={{bottom: 12}}
          flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
        >
          {view === 'table' ? (
            <TextInput
              value={filter}
              style={{minWidth: 250}}
              icon="search"
              onChange={(e) => setFilter(e.target.value)}
              placeholder="Filter metadata keys"
            />
          ) : (
            <ButtonGroup
              activeItems={new Set([plotView])}
              onClick={(id: 'partition' | 'time') => {
                setPlotView(id);
              }}
              buttons={[
                {id: 'partition', label: 'Partitions', icon: 'partition'},
                {id: 'time', label: 'Events', icon: 'materialization'},
              ]}
            />
          )}
          <ButtonGroup
            activeItems={new Set([view])}
            onClick={(id: 'table' | 'plots') => {
              setView(id);
            }}
            buttons={[
              {id: 'table', icon: 'table_view', label: 'Table'},
              {id: 'plots', icon: 'asset_plot', label: 'Plots'},
            ]}
          />
        </Box>
      )}
      {view === 'table' ? (
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
              {filteredRows.length === 0 && (
                <tr>
                  <td colSpan={4}>
                    <Caption color={Colors.textLight()}>No metadata entries</Caption>
                  </td>
                </tr>
              )}
              {filteredRows
                .slice(0, displayedCount)
                .map(({entry, timestamp, runId, icon, tooltip}) => (
                  <tr key={`metadata-${timestamp}-${entry.label}`}>
                    <td>
                      <Mono>{entry.label}</Mono>
                    </td>
                    {showTimestamps && (
                      <td>
                        <Tooltip content={tooltip}>
                          <Tag>
                            <Box flex={{gap: 4, alignItems: 'center'}}>
                              <Icon name={icon} />
                              <Timestamp timestamp={{ms: Number(timestamp)}} />
                            </Box>
                          </Tag>
                        </Tooltip>
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
          {displayedCount < filteredRows.length ? (
            <Box padding={{vertical: 8}}>
              <Button small onClick={() => setDisplayedCount(Number.MAX_SAFE_INTEGER)}>
                Show {filteredRows.length - displayedCount} more
              </Button>
            </Box>
          ) : displayedCount > displayedByDefault ? (
            <Box padding={{vertical: 8}}>
              <Button small onClick={() => setDisplayedCount(displayedByDefault)}>
                Show less
              </Button>
            </Box>
          ) : undefined}
        </AssetEventMetadataScrollContainer>
      ) : null}
      {view === 'plots' ? (
        <AssetEventMetadataPlots
          assetKey={assetKey}
          params={plotView === 'partition' ? {partition: ''} : {time: ''}}
          assetHasDefinedPartitions={!!assetHasDefinedPartitions}
        />
      ) : null}
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
  /** -2 accounts for the left and right border, which are not taken into account
  * and cause a tiny amount of horizontal scrolling at all times. */
  width: calc(100% - 2px);
  border-spacing: 0;
  border-collapse: collapse;

  & > thead > tr > td {
    color: ${Colors.textLighter()};
    font-size: 12px;
    line-height: 16px;
  }

  & > tbody > tr > td,
  & > thead > tr > td {
    border: 1px solid ${Colors.keylineDefault()};
    padding: 8px 12px;
    font-size: 14px;
    line-height: 20px;
    vertical-align: top;

    &:first-child {
      max-width: 300px;
      word-wrap: break-word;
      width: 25%;
    }
  }
`;

function isEntryHidden(
  entry: MetadataEntryLabelOnly,
  {hideEntriesShownOnOverview}: {hideEntriesShownOnOverview: boolean | undefined},
) {
  // Used by our libraries eg: dagster_dbt
  if (HIDDEN_METADATA_ENTRY_LABELS.has(entry.label)) {
    return true;
  }
  // Used to implement features, never shown in the metadata table
  if (isCanonicalColumnLineageEntry(entry) || isCanonicalCodeSourceEntry(entry)) {
    return true;
  }
  // Shown in the right panel on asset overview, but still human readable
  // and displayed on other pages.
  if (
    hideEntriesShownOnOverview &&
    (isCanonicalColumnSchemaEntry(entry) ||
      isCanonicalRowCountMetadataEntry(entry) ||
      isCanonicalTableNameEntry(entry) ||
      isCanonicalUriEntry(entry))
  ) {
    return true;
  }
  return false;
}
