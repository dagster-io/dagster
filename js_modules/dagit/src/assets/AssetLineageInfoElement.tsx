import React from 'react';
import {Link} from 'react-router-dom';

import {AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_assetLineage} from 'src/assets/types/AssetQuery';

export const AssetLineageInfoElement: React.FunctionComponent<{
  lineage_info: AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_assetLineage;
}> = ({lineage_info}) => {
  const partition_list_label = lineage_info.partitions.length == 1 ? 'Partition' : 'Partitions';
  const partition_list_str = lineage_info.partitions
    .map((partition) => `"${partition}"`)
    .join(', ');
  const parent_partition_phrase = (
    <>
      {partition_list_label} {partition_list_str} of{' '}
    </>
  );
  return (
    <>
      {lineage_info.partitions.length > 0 ? parent_partition_phrase : ''}
      <Link to={`/instance/assets/${lineage_info.assetKey.path.map(encodeURIComponent).join('/')}`}>
        {lineage_info.assetKey.path.join(' > ')}
      </Link>
    </>
  );
};
