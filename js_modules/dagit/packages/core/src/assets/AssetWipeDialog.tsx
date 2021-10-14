import {gql, RefetchQueriesFunction, useMutation} from '@apollo/client';
import * as React from 'react';

import {ButtonWIP} from '../ui/Button';
import {DialogBody, DialogFooter, DialogWIP} from '../ui/Dialog';
import {Group} from '../ui/Group';

interface AssetKey {
  path: string[];
}

export const AssetWipeDialog: React.FC<{
  assetKeys: AssetKey[];
  isOpen: boolean;
  onClose: () => void;
  onComplete: (assetKeys: AssetKey[]) => void;
  requery?: RefetchQueriesFunction;
}> = ({assetKeys, isOpen, onClose, onComplete, requery}) => {
  const [requestWipe] = useMutation(ASSET_WIPE_MUTATION, {
    variables: {assetKeys: assetKeys.map((key) => ({path: key.path || []}))},
    refetchQueries: requery,
  });

  const wipe = async () => {
    if (!assetKeys.length) {
      return;
    }
    await requestWipe();
    onComplete(assetKeys);
  };

  return (
    <DialogWIP isOpen={isOpen} title="Wipe assets?" onClose={onClose} style={{width: 400}}>
      <DialogBody>
        <Group direction="column" spacing={8}>
          <div>
            {assetKeys.length === 1 ? (
              <>
                The asset <code>{assetKeys[0].path.join(' > ')}</code> will be wiped.
              </>
            ) : (
              <>{assetKeys.length} assets will be wiped.</>
            )}
          </div>
          <strong>Wiping assets cannot be undone.</strong>
        </Group>
      </DialogBody>
      <DialogFooter>
        <ButtonWIP intent="none" onClick={onClose}>
          Cancel
        </ButtonWIP>
        <ButtonWIP intent="danger" onClick={wipe}>
          Wipe
        </ButtonWIP>
      </DialogFooter>
    </DialogWIP>
  );
};

const ASSET_WIPE_MUTATION = gql`
  mutation AssetWipeMutation($assetKeys: [AssetKeyInput!]!) {
    wipeAssets(assetKeys: $assetKeys) {
      ... on AssetWipeSuccess {
        assetKeys {
          path
        }
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
`;
