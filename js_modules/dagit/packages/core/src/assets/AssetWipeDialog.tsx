import {gql, RefetchQueriesFunction, useMutation} from '@apollo/client';
import {Button, Classes, Dialog} from '@blueprintjs/core';
import * as React from 'react';

interface AssetKey {
  path: string[];
}

export const AssetWipeDialog: React.FC<{
  assetKey?: AssetKey;
  onClose: () => void;
  onComplete: (assetKey: AssetKey) => void;
  requery?: RefetchQueriesFunction;
}> = ({assetKey, onClose, onComplete, requery}) => {
  const [requestWipe] = useMutation(ASSET_WIPE_MUTATION, {
    variables: {assetKey: {path: assetKey?.path || []}},
    refetchQueries: requery,
  });

  const wipe = async () => {
    if (!assetKey) {
      return;
    }
    await requestWipe();
    onComplete(assetKey);
  };

  const title = (
    <>
      Wipe asset <code>{assetKey?.path.join(' > ')}</code>
    </>
  );
  return (
    <Dialog isOpen={!!assetKey} title={title} onClose={onClose} style={{width: 800}}>
      <div className={Classes.DIALOG_BODY}>Wiping the asset cannot be undone.</div>
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
  mutation AssetWipeMutation($assetKey: AssetKeyInput!) {
    wipeAsset(assetKey: $assetKey) {
      ... on AssetWipeSuccess {
        assetKey {
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
