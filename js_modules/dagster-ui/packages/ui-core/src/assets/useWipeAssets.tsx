import {useLayoutEffect, useRef, useState} from 'react';

import {RefetchQueriesFunction, gql, useMutation} from '../apollo-client';
import {AssetWipeMutation, AssetWipeMutationVariables} from './types/useWipeAssets.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PartitionsByAssetSelector} from '../graphql/types';

const CHUNK_SIZE = 100;

export function useWipeAssets({
  refetchQueries,
  onClose,
  onComplete,
}: {
  refetchQueries: RefetchQueriesFunction | undefined;
  onClose: () => void;
  onComplete?: () => void;
}) {
  const [requestWipe] = useMutation<AssetWipeMutation, AssetWipeMutationVariables>(
    ASSET_WIPE_MUTATION,
    {refetchQueries},
  );

  const [isWiping, setIsWiping] = useState(false);
  const [wipedCount, setWipedCount] = useState(0);
  const [failedCount, setFailedCount] = useState(0);

  const isDone = !isWiping && (wipedCount || failedCount);

  const didCancel = useRef(false);

  const wipeAssets = async (assetPartitionRanges: PartitionsByAssetSelector[]) => {
    if (!assetPartitionRanges.length) {
      return;
    }
    setIsWiping(true);
    for (let i = 0, l = assetPartitionRanges.length; i < l; i += CHUNK_SIZE) {
      if (didCancel.current) {
        return;
      }
      const nextChunk = assetPartitionRanges.slice(i, i + CHUNK_SIZE);
      const result = await requestWipe({
        variables: {assetPartitionRanges: nextChunk},
        refetchQueries,
      });
      const data = result.data?.wipeAssets;
      switch (data?.__typename) {
        case 'AssetNotFoundError':
        case 'PythonError':
          setFailedCount((failed) => failed + nextChunk.length);
          break;
        case 'AssetWipeSuccess':
          setWipedCount((wiped) => wiped + nextChunk.length);
          break;
        case 'UnauthorizedError':
          showCustomAlert({
            title: 'Could not wipe asset materializations',
            body: 'You do not have permission to do this.',
          });
          onClose();
          return;
      }
    }
    onComplete?.();
    setIsWiping(false);
  };

  useLayoutEffect(() => {
    return () => {
      didCancel.current = true;
    };
  }, []);

  return {wipeAssets, isWiping, isDone, wipedCount, failedCount};
}

export const ASSET_WIPE_MUTATION = gql`
  mutation AssetWipeMutation($assetPartitionRanges: [PartitionsByAssetSelector!]!) {
    wipeAssets(assetPartitionRanges: $assetPartitionRanges) {
      ... on AssetWipeSuccess {
        assetPartitionRanges {
          assetKey {
            path
          }
          partitionRange {
            start
            end
          }
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
