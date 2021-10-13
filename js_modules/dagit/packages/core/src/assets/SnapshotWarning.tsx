import {gql} from '@apollo/client';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {Timestamp} from '../app/time/Timestamp';
import {Alert} from '../ui/Alert';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';

import {SnapshotWarningAssetFragment} from './types/SnapshotWarningAssetFragment';

export const SnapshotWarning: React.FC<{
  asset: SnapshotWarningAssetFragment;
  asOf: string | null;
}> = ({asOf, asset}) => {
  // If the most recent materialization and the `asOf` materialization are the same, we don't
  // want to show the `Alert`.
  if (!asOf) {
    return null;
  }

  const materializationAsOfTime = asset.assetMaterializations[0];
  const mostRecentMaterialization = asset.mostRecentMaterialization[0];

  if (
    !materializationAsOfTime ||
    !mostRecentMaterialization ||
    materializationAsOfTime.materializationEvent.timestamp ===
      mostRecentMaterialization.materializationEvent.timestamp
  ) {
    return null;
  }

  return (
    <Box
      padding={{vertical: 16, horizontal: 24}}
      border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
    >
      <Alert
        intent="info"
        title="This is a historical asset snapshot."
        description={
          <span>
            This view represents{' '}
            <span style={{fontWeight: 600}}>{asset.key.path[asset.key.path.length - 1]}</span> as of{' '}
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
    </Box>
  );
};

export const SNAPSHOT_WARNING_ASSET_FRAGMENT = gql`
  fragment SnapshotWarningAssetFragment on Asset {
    id
    key {
      path
    }
    mostRecentMaterialization: assetMaterializations(limit: 1) {
      materializationEvent {
        timestamp
      }
    }
    assetMaterializations(limit: $limit, beforeTimestampMillis: $before) {
      materializationEvent {
        timestamp
      }
    }
  }
`;
