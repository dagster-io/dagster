import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import qs from 'qs';
import React from 'react';
import {Link} from 'react-router-dom';

import {Timestamp} from '../app/time/Timestamp';
import {Box} from '../ui/Box';
import {ButtonLink} from '../ui/ButtonLink';
import {Group} from '../ui/Group';

import {AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_assetLineage} from './types/AssetQuery';

const AssetLineageInfoElement: React.FC<{
  lineage_info: AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_assetLineage;
  timestamp: string;
}> = ({lineage_info, timestamp}) => {
  const partition_list_label = lineage_info.partitions.length === 1 ? 'Partition' : 'Partitions';
  const partition_list_str = lineage_info.partitions
    .map((partition) => `"${partition}"`)
    .join(', ');
  const to = `/instance/assets/${lineage_info.assetKey.path
    .map(encodeURIComponent)
    .join('/')}?${qs.stringify({asOf: timestamp})}`;

  return (
    <Group direction="row" spacing={8} alignItems="center">
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
                    <React.Fragment key={`${ii}-space`}>{`&nbsp;>&nbsp;`}</React.Fragment>
                  ) : null,
                  curr,
                ],
                [] as React.ReactNode[],
              )}
          </Box>
        </Link>
      </Tooltip>
    </Group>
  );
};

const MAX_COLLAPSED = 5;

export const AssetLineageElements: React.FunctionComponent<{
  elements: AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_assetLineage[];
  timestamp: string;
}> = ({elements, timestamp}) => {
  const [collapsed, setCollapsed] = React.useState(true);

  return (
    <Group direction="column" spacing={4}>
      {elements.length > MAX_COLLAPSED && (
        <ButtonLink onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? 'Show More' : 'Show Less'}
        </ButtonLink>
      )}
      {(collapsed ? elements.slice(elements.length - MAX_COLLAPSED) : elements).map((info, idx) => (
        <AssetLineageInfoElement key={idx} lineage_info={info} timestamp={timestamp} />
      ))}
    </Group>
  );
};
