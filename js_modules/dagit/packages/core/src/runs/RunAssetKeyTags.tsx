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

export const RunAssetKeyTags: React.FC<{
  assetKeys: AssetKey[] | null;
  clickableTags?: boolean;
}> = React.memo(({assetKeys, clickableTags}) => {
  const [showMore, setShowMore] = React.useState(false);

  if (!assetKeys || !assetKeys.length) {
    return null;
  }

  const displayed = assetKeys.slice(0, 3);
  const hidden = assetKeys.length - displayed.length;

  if (clickableTags) {
    return (
      <>
        {displayed.map((assetKey) => (
          <Link to={assetDetailsPathForKey(assetKey)} key={tokenForAssetKey(assetKey)}>
            <Tag intent="none" interactive icon="asset">
              {displayNameForAssetKey(assetKey)}
            </Tag>
          </Link>
        ))}
        {hidden > 0 && (
          <ButtonLink onClick={() => setShowMore(true)}>
            <Tag intent="none" icon="asset">
              {` + ${hidden} more`}
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
                    <th>Asset Key</th>
                  </tr>
                </thead>
                <tbody>
                  {assetKeys.map((assetKey) => (
                    <tr key={tokenForAssetKey(assetKey)}>
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
            <Button intent="primary" autoFocus={true} onClick={() => setShowMore(false)}>
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
