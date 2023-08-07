import {Box, Caption, Colors, Mono} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import uniqBy from 'lodash/uniqBy';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {MetadataEntry} from '../metadata/MetadataEntry';
import {titleForRun} from '../runs/RunUtils';

import {
  AssetObservationFragment,
  AssetMaterializationFragment,
} from './types/useRecentAssetEvents.types';

/**
 * This component shows the metadata entries attached to an Asset Materialization or Observation event.
 * AssetNodes also have definition-time metadata, which is unrelated to this event metadata.
 */
export const AssetEventMetadataEntriesTable: React.FC<{
  event: AssetObservationFragment | AssetMaterializationFragment | null;
  observations?: (AssetObservationFragment | AssetMaterializationFragment)[];
}> = ({event, observations}) => {
  if (!event || (!event.metadataEntries.length && !observations?.length)) {
    return <Caption color={Colors.Gray500}>No metadata entries</Caption>;
  }
  const {metadataEntries, timestamp} = event;

  // If there are multiple observation events that contain entries with the same label,
  // only include the latest (newest) line for that metadata label in the table.
  const observationEntries = uniqBy(
    (observations || []).flatMap((o) =>
      o.metadataEntries.map((entry) => ({timestamp: o.timestamp, runId: o.runId, entry})),
    ),
    (e) => e.entry.label,
  );

  return (
    <AssetEventMetadataScrollContainer>
      <AssetEventMetadataTable>
        <tbody>
          {metadataEntries.map((entry) => (
            <tr key={`metadata-${entry.label}`}>
              <td>
                <Mono>{entry.label}</Mono>
              </td>
              <td>
                <Mono>
                  <MetadataEntry entry={entry} expandSmallValues={true} />
                </Mono>
              </td>
              <td style={{opacity: 0.7}}>{entry.description}</td>
            </tr>
          ))}
          {observationEntries.map((obv) => (
            <tr key={`metadata-${obv.timestamp}-${obv.entry.label}`}>
              <td>
                <Mono>{obv.entry.label}</Mono>
              </td>
              <td>
                <Mono>
                  <MetadataEntry entry={obv.entry} expandSmallValues={true} />
                </Mono>
              </td>
              <td style={{opacity: 0.7}}>
                <Box>
                  {`Observed in run `}
                  <Link to={`/runs/${obv.runId}?timestamp=${timestamp}`}>
                    <Mono>{titleForRun({id: obv.runId})}</Mono>
                  </Link>
                </Box>
                <Caption>
                  {`(${dayjs(Number(obv.timestamp)).from(
                    Number(timestamp),
                    true /* withoutSuffix */,
                  )} later)`}
                </Caption>
                {obv.entry.description}
              </td>
            </tr>
          ))}
        </tbody>
      </AssetEventMetadataTable>
    </AssetEventMetadataScrollContainer>
  );
};

const AssetEventMetadataScrollContainer = styled.div`
  width: 100%;
  overflow-x: auto;
`;

const AssetEventMetadataTable = styled.table`
  width: 100%;
  border-spacing: 0;
  border-collapse: collapse;
  tr td:first-child {
    max-width: 300px;
    word-wrap: break-word;
    width: 25%;
  }
  tr td {
    border: 1px solid ${Colors.KeylineGray};
    padding: 8px 12px;
    font-size: 14px;
    vertical-align: top;
  }
`;
