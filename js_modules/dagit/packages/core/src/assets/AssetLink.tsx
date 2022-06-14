import {Box, Colors, Icon} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';

export const AssetLink: React.FC<{
  path: string[];
  icon?: 'asset' | 'asset_non_sda' | 'folder';
  url?: string;
  isGroup?: boolean;
}> = ({path, icon, url, isGroup}) => {
  const linkUrl = url ? url : assetDetailsPathForKey({path});

  return (
    <Box flex={{direction: 'row', alignItems: 'center', display: 'inline-flex'}}>
      {icon ? (
        <Box margin={{right: 8}}>
          <Icon name={icon} color={Colors.Gray400} />
        </Box>
      ) : null}
      <Link to={linkUrl}>
        <span style={{wordBreak: 'break-word'}}>
          {path
            .map((p, i) => <span key={i}>{p}</span>)
            .reduce(
              (accum, curr, ii) => [
                ...accum,
                ii > 0 ? <React.Fragment key={`${ii}-space`}>&nbsp;/&nbsp;</React.Fragment> : null,
                curr,
              ],
              [] as React.ReactNode[],
            )}
          {isGroup ? '/' : null}
        </span>
      </Link>
    </Box>
  );
};
