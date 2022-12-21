import {Box, Caption, Colors, Icon, Mono} from '@dagster-io/ui';
import dayjs from 'dayjs';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {MetadataEntry} from '../metadata/MetadataEntry';
import {titleForRun} from '../runs/RunUtils';

import {AssetMaterializationFragment} from './types/AssetMaterializationFragment';
import {AssetObservationFragment} from './types/AssetObservationFragment';

/**
 * This component shows the metadata entries attached to an Asset Materialization or Observation event.
 * AssetNodes also have definition-time metadata, which is unrelated to this event metadata.
 */
export const AssetEventMetadataEntriesTable: React.FC<{
  event: AssetObservationFragment | AssetMaterializationFragment | null;
  observations?: (AssetObservationFragment | AssetMaterializationFragment)[];
}> = ({event, observations}) => {
  if (!event || (!event.metadataEntries.length && !observations?.length)) {
    return <Caption color={Colors.Gray500}>No materializations</Caption>;
  }

  const {metadataEntries, timestamp} = event;

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

          {(observations || []).map((obs) => (
            <React.Fragment key={obs.timestamp}>
              {obs.metadataEntries.map((entry) => (
                <tr key={`metadata-${obs.timestamp}-${entry.label}`}>
                  <td>
                    <Mono>{entry.label}</Mono>
                  </td>
                  <td>
                    <Mono>
                      <MetadataEntry entry={entry} expandSmallValues={true} />
                    </Mono>
                  </td>
                  <td style={{opacity: 0.7}}>
                    <Box flex={{gap: 8}}>
                      <Icon name="observation" size={16} style={{marginTop: 2}} />
                      <span>
                        {`${obs.stepKey} in `}
                        <Link to={`/runs/${obs.runId}?timestamp=${obs.timestamp}`}>
                          <Mono>{titleForRun({runId: obs.runId})}</Mono>
                        </Link>
                      </span>
                    </Box>
                    <Caption style={{marginLeft: 24}}>
                      {`(${dayjs(obs.timestamp).from(timestamp, true /* withoutSuffix */)} later)`}
                    </Caption>
                    {entry.description}
                  </td>
                </tr>
              ))}
            </React.Fragment>
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

export const AssetEventDetailEmpty = () => <Box />;
export const AssetPartitionDetailEmpty = () => <Box />;
