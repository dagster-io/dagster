import React from 'react';
import {Link} from 'react-router-dom';

import {ButtonLink} from '../ui/ButtonLink';

import {AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_assetLineage} from './types/AssetQuery';

const AssetLineageInfoElement: React.FC<{
  lineage_info: AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_assetLineage;
}> = ({lineage_info}) => {
  const partition_list_label = lineage_info.partitions.length == 1 ? 'Partition' : 'Partitions';
  const partition_list_str = lineage_info.partitions
    .map((partition) => `"${partition}"`)
    .join(', ');
  return (
    <div>
      {lineage_info.partitions.length > 0
        ? `${partition_list_label} ${partition_list_str} of `
        : ''}
      <Link to={`/instance/assets/${lineage_info.assetKey.path.map(encodeURIComponent).join('/')}`}>
        {lineage_info.assetKey.path.join(' > ')}
      </Link>
    </div>
  );
};

const MAX_COLLAPSED = 5;

export const AssetLineageElements: React.FunctionComponent<{
  elements: AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_assetLineage[];
}> = ({elements}) => {
  const [collapsed, setCollapsed] = React.useState(true);

  return (
    <div>
      {elements.length > MAX_COLLAPSED && (
        <ButtonLink onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? 'Show More' : 'Show Less'}
        </ButtonLink>
      )}
      {(collapsed ? elements.slice(elements.length - MAX_COLLAPSED) : elements).map((info, idx) => (
        <AssetLineageInfoElement key={idx} lineage_info={info} />
      ))}
    </div>
  );
};
