import {Box, Colors, Icon, MiddleTruncate} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {BlueprintManagerFragment} from './types/WorkspaceBlueprintManagersRoot.types';
import {HeaderCell, HeaderRow, Row, RowCell} from '../ui/VirtualizedTable';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

const TEMPLATE_COLUMNS = '1.5fr 1fr 1fr';

interface BlueprintManagerRowProps extends BlueprintManagerFragment {
  repoAddress: RepoAddress;
  height: number;
  start: number;
}

export const VirtualizedBlueprintManagerRow = (props: BlueprintManagerRowProps) => {
  const {name, repoAddress, start, height} = props;

  return (
    <Row $height={height} $start={start}>
      <RowGrid border="bottom">
        <RowCell>
          <Box flex={{direction: 'column', gap: 4}}>
            <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
              <Icon name="add_circle" color={Colors.accentGray()} />

              <span style={{fontWeight: 500}}>
                <Link to={workspacePathFromAddress(repoAddress, `/blueprint-managers/${name}`)}>
                  <MiddleTruncate text={name} />
                </Link>
              </span>
            </Box>
          </Box>
        </RowCell>
      </RowGrid>
    </Row>
  );
};

export const VirtualizedBlueprintManagerHeader = () => {
  return (
    <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky>
      <HeaderCell>Name</HeaderCell>
    </HeaderRow>
  );
};

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
  height: 100%;
`;
