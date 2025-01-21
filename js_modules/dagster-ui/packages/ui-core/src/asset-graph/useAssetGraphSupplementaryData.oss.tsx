import {AssetKey} from '../assets/types';

export type SupplementaryInformation = Record<string, AssetKey[]> | null | undefined;

// Stub for cloud to supply extended selection syntax filtering capabilities
export const useAssetGraphSupplementaryData = (
  _: string,
): {loading: boolean; data: SupplementaryInformation | null} => {
  return {
    loading: false,
    data: null,
  };
};
