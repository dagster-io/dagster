import {gql, RefetchQueriesFunction, useMutation} from '@apollo/client';
import {Button, DialogBody, DialogFooter, Dialog, Group} from '@dagster-io/ui';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {displayNameForAssetKey} from '../asset-graph/Utils';

import {AssetWipeMutation, AssetWipeMutationVariables} from './types/AssetWipeMutation';

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
  const [requestWipe] = useMutation<AssetWipeMutation, AssetWipeMutationVariables>(
    ASSET_WIPE_MUTATION,
    {
      variables: {assetKeys: assetKeys.map((key) => ({path: key.path || []}))},
      refetchQueries: requery,
    },
  );

  const wipe = async () => {
    if (!assetKeys.length) {
      return;
    }
    await requestWipe();
    onComplete(assetKeys);
  };

  return (
    <Dialog
      isOpen={isOpen}
      title={`Wipe materializations of ${
        assetKeys.length === 1 ? displayNameForAssetKey(assetKeys[0]) : 'selected assets'
      }?`}
      onClose={onClose}
      style={{width: 400}}
    >
      <DialogBody>
        <Group direction="column" spacing={8}>
          <div>
            Assets defined only by their historical materializations will disappear from the Asset
            Catalog. Software-defined assets will remain unless their definition is also deleted
            from the repository.
          </div>
          <strong>This action cannot be undone.</strong>
        </Group>
      </DialogBody>
      <DialogFooter>
        <Button intent="none" onClick={onClose}>
          Cancel
        </Button>
        <Button intent="danger" onClick={wipe}>
          Wipe
        </Button>
      </DialogFooter>
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
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
