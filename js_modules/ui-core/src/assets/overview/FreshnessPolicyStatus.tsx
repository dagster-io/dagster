import {Box, Subtitle2} from '@dagster-io/ui-components';

import {FreshnessTag} from './FreshnessPolicySection';
import {FRESHNESS_EVALUATION_ENABLED_QUERY} from './FreshnessQueries';
import {useQuery} from '../../apollo-client';
import {AssetKey} from '../../graphql/types';
import {FreshnessPolicyFragment} from '../types/FreshnessPolicyFragment.types';
import {
  FreshnessEvaluationEnabledQuery,
  FreshnessEvaluationEnabledQueryVariables,
} from './types/FreshnessQueries.types';

export interface Props {
  freshnessPolicy: FreshnessPolicyFragment;
  assetKey: AssetKey;
}

export const FreshnessPolicyStatus = (props: Props) => {
  const {freshnessPolicy, assetKey} = props;
  const {data} = useQuery<
    FreshnessEvaluationEnabledQuery,
    FreshnessEvaluationEnabledQueryVariables
  >(FRESHNESS_EVALUATION_ENABLED_QUERY);

  if (!data?.instance?.freshnessEvaluationEnabled) {
    return null;
  }

  return (
    <Box flex={{direction: 'column', gap: 6}}>
      <Subtitle2>Freshness policy</Subtitle2>
      <FreshnessTag policy={freshnessPolicy} assetKey={assetKey} />
    </Box>
  );
};
