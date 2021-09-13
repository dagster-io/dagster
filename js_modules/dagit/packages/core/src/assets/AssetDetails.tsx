import {useQuery} from '@apollo/client';
import {Colors, Icon} from '@blueprintjs/core';
import qs from 'qs';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {Timestamp} from '../app/time/Timestamp';
import {PipelineReference} from '../pipelines/PipelineReference';
import {MetadataEntry} from '../runs/MetadataEntry';
import {titleForRun} from '../runs/RunUtils';
import {Alert} from '../ui/Alert';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {MetadataTable} from '../ui/MetadataTable';
import {Spinner} from '../ui/Spinner';
import {Mono, Subheading} from '../ui/Text';

import {AssetLineageElements} from './AssetLineageElements';
import {ASSET_QUERY} from './queries';
import {AssetKey} from './types';
import {AssetQuery, AssetQueryVariables} from './types/AssetQuery';

interface Props {
  assetKey: AssetKey;
  asOf: string | null;
}

export const AssetDetails: React.FC<Props> = ({assetKey, asOf}) => {
  const before = React.useMemo(() => (asOf ? `${Number(asOf) + 1}` : ''), [asOf]);
  const {data, loading} = useQuery<AssetQuery, AssetQueryVariables>(ASSET_QUERY, {
    variables: {
      assetKey: {path: assetKey.path},
      limit: 1,
      before,
    },
  });

  // If the most recent materialization and the `asOf` materialization are the same, we don't
  // want to show the `Alert`.
  const showAlert = React.useMemo(() => {
    if (loading || !asOf) {
      return false;
    }

    const assetOrError = data?.assetOrError;
    if (!assetOrError || assetOrError?.__typename !== 'Asset') {
      return false;
    }

    const materializationAsOfTime = assetOrError.assetMaterializations[0];
    const mostRecentMaterialization = assetOrError.mostRecentMaterialization[0];

    return (
      materializationAsOfTime &&
      mostRecentMaterialization &&
      materializationAsOfTime.materializationEvent.timestamp !==
        mostRecentMaterialization.materializationEvent.timestamp
    );
  }, [asOf, data?.assetOrError, loading]);

  const content = () => {
    if (loading) {
      return (
        <Box padding={{vertical: 20}}>
          <Spinner purpose="section" />
        </Box>
      );
    }

    const assetOrError = data?.assetOrError;

    if (!assetOrError || assetOrError.__typename !== 'Asset') {
      return null;
    }

    const latest = assetOrError.assetMaterializations[0];

    if (!latest) {
      return (
        <div>
          No materializations found at{' '}
          <Timestamp
            timestamp={{ms: Number(asOf)}}
            timeFormat={{showSeconds: true, showTimezone: true}}
          />
          .
        </div>
      );
    }

    const latestEvent = latest.materializationEvent;
    const latestRun = latest.runOrError.__typename === 'PipelineRun' ? latest.runOrError : null;
    const latestAssetLineage = latestEvent?.assetLineage;

    return (
      <MetadataTable
        rows={[
          {
            key: 'Latest materialization from',
            value: latestRun ? (
              <div>
                <div>
                  {'Run '}
                  <Link
                    to={`/instance/runs/${latestEvent.runId}?timestamp=${latestEvent.timestamp}`}
                  >
                    <Mono>{titleForRun({runId: latestEvent.runId})}</Mono>
                  </Link>
                </div>
                <div style={{paddingLeft: 10, paddingTop: 4}}>
                  <PipelineReference
                    showIcon
                    pipelineName={latestRun.pipelineName}
                    pipelineHrefContext="repo-unknown"
                    snapshotId={latestRun.pipelineSnapshotId}
                    mode={latestRun.mode}
                  />
                </div>
                <div style={{paddingLeft: 10, paddingTop: 4}}>
                  <Icon
                    icon="git-commit"
                    color={Colors.GRAY2}
                    iconSize={12}
                    style={{position: 'relative', top: -2, paddingRight: 5}}
                  />
                  <Link
                    to={`/instance/runs/${latestRun.runId}?${qs.stringify({
                      selection: latest.materializationEvent.stepKey,
                      logs: `step:${latest.materializationEvent.stepKey}`,
                    })}`}
                  >
                    {latest.materializationEvent.stepKey}
                  </Link>
                </div>
              </div>
            ) : (
              'No materialization events'
            ),
          },
          latest?.partition
            ? {
                key: 'Latest partition',
                value: latest ? latest.partition : 'No materialization events',
              }
            : undefined,
          {
            key: 'Latest timestamp',
            value: latestEvent ? (
              <Timestamp timestamp={{ms: Number(latestEvent.timestamp)}} />
            ) : (
              'No materialization events'
            ),
          },
          latestAssetLineage?.length
            ? {
                key: 'Latest parent assets',
                value: (
                  <AssetLineageElements
                    elements={latestAssetLineage}
                    timestamp={latestEvent.timestamp}
                  />
                ),
              }
            : undefined,
          ...latestEvent?.materialization.metadataEntries.map((entry) => ({
            key: entry.label,
            value: <MetadataEntry entry={entry} expandSmallValues={true} />,
          })),
        ].filter(Boolean)}
      />
    );
  };

  const isPartitioned = !!(
    data?.assetOrError?.__typename === 'Asset' &&
    data?.assetOrError?.assetMaterializations[0]?.partition
  );

  return (
    <Group direction="column" spacing={16}>
      {showAlert ? (
        <Alert
          intent="info"
          title="This is a historical asset snapshot."
          description={
            <span>
              This view represents{' '}
              <span style={{fontWeight: 600}}>{assetKey.path[assetKey.path.length - 1]}</span> as of{' '}
              <span style={{fontWeight: 600}}>
                <Timestamp
                  timestamp={{ms: Number(asOf)}}
                  timeFormat={{showSeconds: true, showTimezone: true}}
                />
              </span>
              . You can also view the <Link to={location.pathname}>latest materialization</Link> for
              this asset.
            </span>
          }
        />
      ) : null}
      <Subheading>{isPartitioned ? 'Latest Materialized Partition' : 'Details'}</Subheading>
      {content()}
    </Group>
  );
};
