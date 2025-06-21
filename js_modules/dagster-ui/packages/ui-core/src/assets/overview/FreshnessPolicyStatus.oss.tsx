import {AssetKey} from '../../graphql/types';
import {FreshnessPolicyFragment} from '../types/FreshnessPolicyFragment.types';

export interface FreshnessPolicyStatusProps {
  freshnessPolicy: FreshnessPolicyFragment;
  assetKey: AssetKey;
}

export const FreshnessPolicyStatus = (_props: FreshnessPolicyStatusProps) => null;
