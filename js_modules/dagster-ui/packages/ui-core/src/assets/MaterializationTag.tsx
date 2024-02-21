// eslint-disable-next-line no-restricted-imports
import {Box, Colors, Tag} from '@dagster-io/ui-components';

import {AssetKey} from './types';
import {Timestamp} from '../app/time/Timestamp';
import {StatusCase} from '../asset-graph/AssetNodeStatusContent';
import {AssetRunLink} from '../asset-graph/AssetRunLinking';
import {StatusCaseDot} from '../asset-graph/sidebar/util';

export const MaterializationTag = ({
  assetKey,
  event,
  stepKey,
}: {
  assetKey: AssetKey;
  event: {timestamp: string; runId: string};
  stepKey: string | null;
}) => (
  <Tag intent="success">
    <Box flex={{gap: 4, alignItems: 'center'}}>
      <StatusCaseDot statusCase={StatusCase.MATERIALIZED} />
      <AssetRunLink
        assetKey={assetKey}
        runId={event.runId}
        event={{timestamp: event.timestamp, stepKey}}
      >
        <Box style={{color: Colors.textGreen()}} flex={{gap: 4}}>
          <Timestamp timestamp={{ms: Number(event.timestamp)}} />
        </Box>
      </AssetRunLink>
    </Box>
  </Tag>
);
