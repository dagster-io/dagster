import * as React from 'react';
import {Link} from 'react-router-dom';

import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {IconWIP} from '../ui/Icon';

export const AssetLink: React.FC<{
  path: string[];
  displayIcon?: boolean;
  url?: string;
  trailingSlash?: boolean;
}> = ({path, displayIcon, url, trailingSlash}) => {
  const linkUrl = url ? url : `/instance/assets/${path.map(encodeURIComponent).join('/')}`;

  return (
    <Box flex={{direction: 'row', alignItems: 'center', display: 'inline-flex'}}>
      {displayIcon ? (
        <Box margin={{right: 8}}>
          <IconWIP name="asset" color={ColorsWIP.Gray400} />
        </Box>
      ) : null}
      <Link to={linkUrl}>
        <span style={{wordBreak: 'break-word'}}>
          {path
            .map((p, i) => <span key={i}>{p}</span>)
            .reduce(
              (accum, curr, ii) => [
                ...accum,
                ii > 0 ? (
                  <React.Fragment key={`${ii}-space`}>&nbsp;{`>`}&nbsp;</React.Fragment>
                ) : null,
                curr,
              ],
              [] as React.ReactNode[],
            )}
          {trailingSlash ? '/' : null}
        </span>
      </Link>
    </Box>
  );
};
