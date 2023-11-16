import {Box, JoinedButtons, MiddleTruncate, colorTextLight} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {TimeFromNow} from '../ui/TimeFromNow';
import {HeaderCell, RowCell} from '../ui/VirtualizedTable';

import {CodeLocationMenu} from './CodeLocationMenu';
import {ImageName, LocationStatus, ModuleOrPackageOrFile, ReloadButton} from './CodeLocationRowSet';
import {RepositoryCountTags} from './RepositoryCountTags';
import {WorkspaceRepositoryLocationNode} from './WorkspaceContext';
import {buildRepoAddress} from './buildRepoAddress';
import {repoAddressAsHumanString} from './repoAddressAsString';
import {
  WorkspaceLocationNodeFragment,
  WorkspaceRepositoryFragment,
} from './types/WorkspaceContext.types';
import {workspacePathFromAddress} from './workspacePath';

export type CodeLocationRowType =
  | {
      type: 'repository';
      codeLocation: WorkspaceLocationNodeFragment;
      repository: WorkspaceRepositoryFragment;
    }
  | {type: 'error'; node: WorkspaceLocationNodeFragment};

const TEMPLATE_COLUMNS = '3fr 1fr 1fr 240px 160px';

interface ErrorRowProps {
  locationNode: WorkspaceRepositoryLocationNode;
  measure: (node: Element | null) => void;
}

export const VirtualizedCodeLocationErrorRow = (props: ErrorRowProps) => {
  const {locationNode, measure} = props;
  const {name} = locationNode;
  return (
    <div ref={measure}>
      <RowGrid border="bottom">
        <RowCell>
          <MiddleTruncate text={name} />
        </RowCell>
        <RowCell>
          <div>
            <LocationStatus location={name} locationOrError={locationNode} />
          </div>
        </RowCell>
        <RowCell>
          <div style={{whiteSpace: 'nowrap'}}>
            <TimeFromNow unixTimestamp={locationNode.updatedTimestamp} />
          </div>
        </RowCell>
        <RowCell>{'\u2013'}</RowCell>
        <RowCell>
          <JoinedButtons>
            <ReloadButton location={name} />
            <CodeLocationMenu locationNode={locationNode} />
          </JoinedButtons>
        </RowCell>
      </RowGrid>
    </div>
  );
};

interface Props {
  codeLocation: WorkspaceRepositoryLocationNode;
  repository: WorkspaceRepositoryFragment;
  measure: (node: Element | null) => void;
}

export const VirtualizedCodeLocationRow = (props: Props) => {
  const {codeLocation, repository, measure} = props;
  const repoAddress = buildRepoAddress(repository.name, repository.location.name);

  const allMetadata = [...codeLocation.displayMetadata, ...repository.displayMetadata];

  return (
    <div ref={measure}>
      <RowGrid border="bottom">
        <RowCell>
          <Box flex={{direction: 'column', gap: 4}}>
            <div style={{fontWeight: 500}}>
              <Link to={workspacePathFromAddress(repoAddress)}>
                <MiddleTruncate text={repoAddressAsHumanString(repoAddress)} />
              </Link>
            </div>
            <ImageName metadata={allMetadata} />
            <ModuleOrPackageOrFile metadata={allMetadata} />
          </Box>
        </RowCell>
        <RowCell>
          <div>
            <LocationStatus location={repository.name} locationOrError={codeLocation} />
          </div>
        </RowCell>
        <RowCell>
          <div style={{whiteSpace: 'nowrap'}}>
            <TimeFromNow unixTimestamp={codeLocation.updatedTimestamp} />
          </div>
        </RowCell>
        <RowCell>
          <RepositoryCountTags repo={repository} repoAddress={repoAddress} />
        </RowCell>
        <RowCell style={{alignItems: 'flex-end'}}>
          <JoinedButtons>
            <ReloadButton location={codeLocation.name} />
            <CodeLocationMenu locationNode={codeLocation} />
          </JoinedButtons>
        </RowCell>
      </RowGrid>
    </div>
  );
};

export const VirtualizedCodeLocationHeader = () => {
  return (
    <Box
      border="top-and-bottom"
      style={{
        display: 'grid',
        gridTemplateColumns: TEMPLATE_COLUMNS,
        height: '32px',
        fontSize: '12px',
        color: colorTextLight(),
      }}
    >
      <HeaderCell>Name</HeaderCell>
      <HeaderCell>Status</HeaderCell>
      <HeaderCell>Updated</HeaderCell>
      <HeaderCell>Definitions</HeaderCell>
      <HeaderCell style={{textAlign: 'right'}}>Actions</HeaderCell>
    </Box>
  );
};

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
`;
