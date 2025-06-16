import {Box, Popover, Tag} from '@dagster-io/ui-components';

import {AssetKey} from '../../graphql/types';
import {FreshnessPolicyFragment} from '../types/FreshnessPolicyFragment.types';

export interface FreshnessPolicySectionProps {
  assetKey: AssetKey;
  policy: FreshnessPolicyFragment;
}

export const FreshnessPolicySection = (_props: FreshnessPolicySectionProps) => {
  return (
    <Popover
      interactionKind="hover"
      placement="top"
      content={
        <Box padding={{vertical: 16, horizontal: 20}} style={{width: '300px'}}>
          Freshness policies are a new feature under active development and are not evaluated by
          default. See [this github discussion] to learn more.
        </Box>
      }
    >
      <Tag intent="none" icon="no_access">
        Not evaluated
      </Tag>
    </Popover>
  );
};
