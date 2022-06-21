import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogFooter,
  Icon,
  Table,
  Tag,
} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {displayNameForAssetKey, tokenForAssetKey} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetKey} from '../assets/types';

const MAX_ASSET_TAGS = 3;

export const RunAssetKeyTags: React.FC<{
  assetKeys: AssetKey[] | null;
  clickableTags?: boolean;
}> = React.memo(({assetKeys, clickableTags}) => {
  const [showMore, setShowMore] = React.useState(false);

  if (!assetKeys || !assetKeys.length) {
    return null;
  }

  const assetCount = assetKeys.length;
  const displayed = assetCount <= MAX_ASSET_TAGS ? assetKeys : [];
  const hidden = assetCount - displayed.length;

  if (clickableTags) {
    return (
      <>
        {displayed.map((assetKey, ii) => (
          <Link to={assetDetailsPathForKey(assetKey)} key={`${tokenForAssetKey(assetKey)}-${ii}`}>
            <Tag intent="none" interactive icon="asset">
              {displayNameForAssetKey(assetKey)}
            </Tag>
          </Link>
        ))}
        {hidden > 0 && (
          <ButtonLink onClick={() => setShowMore(true)}>
            <Tag intent="none" icon="asset">
              {hidden} assets
            </Tag>
          </ButtonLink>
        )}
        <Dialog
          title="Assets in Run"
          onClose={() => setShowMore(false)}
          style={{minWidth: '400px', maxWidth: '80vw', maxHeight: '70vh'}}
          isOpen={showMore}
        >
          {showMore ? (
            <Box
              padding={{bottom: 12}}
              border={{side: 'bottom', color: Colors.KeylineGray, width: 1}}
              style={{overflowY: 'auto'}}
              background={Colors.White}
            >
              <Table>
                <thead>
                  <tr>
                    <th>Asset key</th>
                  </tr>
                </thead>
                <tbody>
                  {assetKeys.map((assetKey, ii) => (
                    <tr key={`${tokenForAssetKey(assetKey)}-${ii}`}>
                      <td>
                        <Link
                          to={assetDetailsPathForKey(assetKey)}
                          key={tokenForAssetKey(assetKey)}
                        >
                          {displayNameForAssetKey(assetKey)}
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Box>
          ) : null}
          <DialogFooter>
            <Button intent="primary" autoFocus onClick={() => setShowMore(false)}>
              OK
            </Button>
          </DialogFooter>
        </Dialog>
      </>
    );
  }

  return (
    <Box flex={{direction: 'row', gap: 8, wrap: 'wrap', alignItems: 'center'}}>
      <Icon color={Colors.Gray400} name="asset" size={16} />
      {`${displayed.map(displayNameForAssetKey).join(', ')}${
        hidden > 0 ? ` + ${hidden} more` : ''
      }`}
    </Box>
  );
});
