import {Box, Colors, Tag} from '@dagster-io/ui-components';

import {AssetKey} from './types';
import {StatusCase} from '../asset-graph/AssetNodeStatusContent';
import {AssetRunLink} from '../asset-graph/AssetRunLinking';
import {StatusCaseDot} from '../asset-graph/sidebar/util';
import {TimeFromNow} from '../ui/TimeFromNow';

export const MaterializationTag = ({
  assetKey,
  event,
  stepKey,
}: {
  assetKey: AssetKey;
  event: {timestamp: string; runId: string};
  stepKey: string | null;
}) => {
  const timestamp = Number(event.timestamp) / 1000;
  return (
    <Tag intent="success">
      <Box flex={{gap: 4, alignItems: 'center'}}>
        <StatusCaseDot statusCase={StatusCase.MATERIALIZED} />
        <AssetRunLink
          assetKey={assetKey}
          runId={event.runId}
          event={{timestamp: event.timestamp, stepKey}}
        >
          <Box style={{color: Colors.textGreen()}} flex={{gap: 4}}>
            <TimeFromNow unixTimestamp={timestamp} />
          </Box>
        </AssetRunLink>
      </Box>
    </Tag>
  );
};
