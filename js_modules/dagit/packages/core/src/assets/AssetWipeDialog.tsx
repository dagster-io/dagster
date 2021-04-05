import {gql, RefetchQueriesFunction, useMutation} from '@apollo/client';
import {Button, Classes, Dialog} from '@blueprintjs/core';
import * as React from 'react';

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

  const title =
    assetKeys.length == 1 ? (
      <>
        Wipe asset <code>{assetKeys[0].path.join(' > ')}</code>
      </>
    ) : (
      <>Wipe {assetKeys.length} assets</>
    );
  return (
    <Dialog isOpen={isOpen} title={title} onClose={onClose} style={{width: 800}}>
      <div className={Classes.DIALOG_BODY}>Wiping assets cannot be undone.</div>
      <div className={Classes.DIALOG_FOOTER}>
        <div className={Classes.DIALOG_FOOTER_ACTIONS}>
          <Button intent="danger" onClick={wipe}>
            Wipe
          </Button>
          <Button intent="none" onClick={onClose}>
            Cancel
          </Button>
        </div>
      </div>
    </Dialog>
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
