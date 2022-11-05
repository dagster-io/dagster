import {Box, Colors, Icon, MiddleTruncate} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';

export const AssetLink: React.FC<{
  path: string[];
  icon?: 'asset' | 'asset_non_sda' | 'folder';
  textStyle?: 'break-word' | 'middle-truncate';
  url?: string;
  isGroup?: boolean;
}> = (props) => {
  const {path, icon, url, isGroup, textStyle = 'break-word'} = props;
  const linkUrl = url ? url : assetDetailsPathForKey({path});
  const assetPath =
    path
      .reduce((accum, elem, ii) => [...accum, ii > 0 ? ' / ' : '', elem], [] as string[])
      .join('') + (isGroup ? '/' : '');

  return (
    <Box
      flex={{direction: 'row', alignItems: 'flex-start', display: 'inline-flex'}}
      style={{maxWidth: '100%'}}
    >
      {icon ? (
        <Box margin={{right: 8, top: 2}}>
          <Icon name={icon} color={Colors.Gray400} />
        </Box>
      ) : null}
      <Link to={linkUrl} style={{overflow: 'hidden'}}>
        {textStyle === 'break-word' ? (
          <span style={{wordBreak: 'break-word'}}>{assetPath}</span>
        ) : (
          <MiddleTruncate text={assetPath} />
        )}
      </Link>
    </Box>
  );
};
