import {Box, Caption, Colors, Icon, MiddleTruncate, Mono, Tooltip} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {succinctType} from './ResourceRoot';
import {HeaderCell, HeaderRow, Row, RowCell} from '../ui/VirtualizedTable';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';
import {ResourceEntryFragment} from './types/WorkspaceResourcesQuery.types';

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
    schedulesUsing,
    sensorsUsing,
  } = props;
  const resourceTypeSuccinct = succinctType(resourceType);
  const uses =
    parentResources.length +
    jobsOpsUsing.length +
    assetKeysUsing.length +
    schedulesUsing.length +
    sensorsUsing.length;

  return (
    <Row $height={height} $start={start}>
      <RowGrid border="bottom">
        <RowCell>
          <Box flex={{direction: 'column', gap: 4}}>
            <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
              <Icon name="resource" color={Colors.accentGray()} />

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
                  color: Colors.textLight(),
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
    <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky>
      <HeaderCell>Name</HeaderCell>
      <HeaderCell>Type</HeaderCell>
      <HeaderCell>Uses</HeaderCell>
    </HeaderRow>
  );
};

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
  height: 100%;
`;
