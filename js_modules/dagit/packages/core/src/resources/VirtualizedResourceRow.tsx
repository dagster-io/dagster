import {Box, Caption, Colors, Icon, MiddleTruncate, Mono, Tooltip} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {HeaderCell, Row, RowCell} from '../ui/VirtualizedTable';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {succinctType} from './ResourceRoot';
import {ResourceEntryFragment} from './types/WorkspaceResourcesRoot.types';

const TEMPLATE_COLUMNS = '1.5fr 1fr 1fr';

interface ResourceRowProps extends ResourceEntryFragment {
  repoAddress: RepoAddress;
  height: number;
  start: number;
}

export const VirtualizedResourceRow = (props: ResourceRowProps) => {
  const {
    name,
    description,
    repoAddress,
    start,
    height,
    resourceType,
    parentResources,
    jobsOpsUsing,
    assetKeysUsing,
  } = props;
  const resourceTypeSuccinct = succinctType(resourceType);
  const uses = parentResources.length + jobsOpsUsing.length + assetKeysUsing.length;

  return (
    <Row $height={height} $start={start}>
      <RowGrid border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}>
        <RowCell>
          <Box flex={{direction: 'column', gap: 4}}>
            <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
              <Icon name="resource" color={Colors.Gray400} />

              <span style={{fontWeight: 500}}>
                <Link to={workspacePathFromAddress(repoAddress, `/resources/${name}`)}>
                  <MiddleTruncate text={name} />
                </Link>
              </span>
            </Box>
            <div
              style={{
                maxWidth: '100%',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              <Caption
                style={{
                  color: Colors.Gray500,
                  whiteSpace: 'nowrap',
                }}
              >
                {description}
              </Caption>
            </div>
          </Box>
        </RowCell>
        <RowCell>
          <Tooltip content={resourceType}>
            <Mono>{resourceTypeSuccinct}</Mono>
          </Tooltip>
        </RowCell>
        <RowCell>
          <Link to={workspacePathFromAddress(repoAddress, `/resources/${name}/uses`)}>{uses}</Link>
        </RowCell>
      </RowGrid>
    </Row>
  );
};

export const VirtualizedResourceHeader = () => {
  return (
    <Box
      border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
      style={{
        display: 'grid',
        gridTemplateColumns: TEMPLATE_COLUMNS,
        height: '32px',
        fontSize: '12px',
        color: Colors.Gray600,
      }}
    >
      <HeaderCell>Name</HeaderCell>
      <HeaderCell>Type</HeaderCell>
      <HeaderCell>Uses</HeaderCell>
    </Box>
  );
};

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
  height: 100%;
`;
