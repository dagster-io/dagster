import {gql} from '@apollo/client';
import {Box, ButtonLink, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetLineageFragment} from './types/AssetLineageElements.types';
import {Timestamp} from '../app/time/Timestamp';

const AssetLineageInfoElement = ({
  lineage_info,
  timestamp,
}: {
  lineage_info: AssetLineageFragment;
  timestamp: string;
}) => {
  const partition_list_label = lineage_info.partitions.length === 1 ? 'Partition' : 'Partitions';
  const partition_list_str = lineage_info.partitions
    .map((partition) => `"${partition}"`)
    .join(', ');
  const to = assetDetailsPathForKey(lineage_info.assetKey, {asOf: timestamp});

  return (
    <Box margin={{bottom: 4}}>
      {lineage_info.partitions.length > 0
        ? `${partition_list_label} ${partition_list_str} of `
        : ''}
      <Tooltip
        content={
          <>
            View snapshot as of{' '}
            <Timestamp
              timestamp={{ms: Number(timestamp)}}
              timeFormat={{showSeconds: true, showTimezone: true}}
            />
          </>
        }
        modifiers={{offset: {enabled: true, options: {offset: [0, 16]}}}}
        placement="right"
      >
        <Link to={to}>
          <Box flex={{display: 'inline-flex', alignItems: 'center'}}>
            {lineage_info.assetKey.path
              .map((p, i) => <span key={i}>{p}</span>)
              .reduce(
                (accum, curr, ii) => [
                  ...accum,
                  ii > 0 ? (
                    <React.Fragment key={`${ii}-space`}>&nbsp;{'>'}&nbsp;</React.Fragment>
                  ) : null,
                  curr,
                ],
                [] as React.ReactNode[],
              )}
          </Box>
        </Link>
      </Tooltip>
    </Box>
  );
};

const MAX_COLLAPSED = 5;

export const AssetLineageElements = ({
  elements,
  timestamp,
}: {
  elements: AssetLineageFragment[];
  timestamp: string;
}) => {
  const [collapsed, setCollapsed] = React.useState(true);

  return (
    <div>
      {elements.length > MAX_COLLAPSED && (
        <ButtonLink onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? 'Show More' : 'Show Less'}
        </ButtonLink>
      )}
      {(collapsed ? elements.slice(elements.length - MAX_COLLAPSED) : elements).map((info, idx) => (
        <AssetLineageInfoElement key={idx} lineage_info={info} timestamp={timestamp} />
      ))}
    </div>
  );
};

export const ASSET_LINEAGE_FRAGMENT = gql`
  fragment AssetLineageFragment on AssetLineageInfo {
    assetKey {
      path
    }
    partitions
  }
`;
