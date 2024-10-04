import {Box, JoinedButtons, MiddleTruncate} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {CodeLocationMenu} from './CodeLocationMenu';
import {ImageName, LocationStatus, ModuleOrPackageOrFile, ReloadButton} from './CodeLocationRowSet';
import {RepositoryCountTags} from './RepositoryCountTags';
import {WorkspaceRepositoryLocationNode} from './WorkspaceContext/WorkspaceContext';
import {
  LocationStatusEntryFragment,
  WorkspaceLocationNodeFragment,
  WorkspaceRepositoryFragment,
} from './WorkspaceContext/types/WorkspaceQueries.types';
import {buildRepoAddress} from './buildRepoAddress';
import {repoAddressAsHumanString} from './repoAddressAsString';
import {workspacePathFromAddress} from './workspacePath';
import {TimeFromNow} from '../ui/TimeFromNow';
import {HeaderCell, HeaderRow, RowCell} from '../ui/VirtualizedTable';

export type CodeLocationRowStatusType = 'Failed' | 'Updating' | 'Loaded' | 'Loading';

export type CodeLocationRowType =
  | {
      type: 'repository';
      locationStatus: LocationStatusEntryFragment;
      locationEntry: WorkspaceLocationNodeFragment;
      repository: WorkspaceRepositoryFragment;
      status: CodeLocationRowStatusType;
    }
  | {
      type: 'location';
      locationStatus: LocationStatusEntryFragment;
      locationEntry: WorkspaceLocationNodeFragment | null;
      status: CodeLocationRowStatusType;
    };

const TEMPLATE_COLUMNS = '3fr 1fr 1fr 160px';

interface LocationRowProps {
  locationEntry: WorkspaceRepositoryLocationNode | null;
  locationStatus: LocationStatusEntryFragment;
  index: number;
}

export const VirtualizedCodeLocationRow = React.forwardRef(
  (props: LocationRowProps, ref: React.ForwardedRef<HTMLDivElement>) => {
    const {locationEntry, locationStatus, index} = props;
    const {name} = locationStatus;
    return (
      <div ref={ref} data-index={index}>
        <RowGrid border="bottom">
          <RowCell>
            <MiddleTruncate text={name} />
          </RowCell>
          <RowCell>
            <div>
              <LocationStatus locationStatus={locationStatus} locationOrError={locationEntry} />
            </div>
          </RowCell>
          <RowCell>
            <div style={{whiteSpace: 'nowrap'}}>
              <TimeFromNow unixTimestamp={locationStatus.updateTimestamp} />
            </div>
          </RowCell>
          <RowCell>
            <JoinedButtons>
              <ReloadButton location={name} />
              {locationEntry ? <CodeLocationMenu locationNode={locationEntry} /> : null}
            </JoinedButtons>
          </RowCell>
        </RowGrid>
      </div>
    );
  },
);

interface RepoRowProps {
  locationEntry: WorkspaceRepositoryLocationNode;
  locationStatus: LocationStatusEntryFragment;
  repository: WorkspaceRepositoryFragment;
  index: number;
  // measure: (node: Element | null) => void;
}

export const VirtualizedCodeLocationRepositoryRow = React.forwardRef(
  (props: RepoRowProps, ref: React.ForwardedRef<HTMLDivElement>) => {
    const {locationEntry, locationStatus, repository, index} = props;
    const repoAddress = buildRepoAddress(repository.name, repository.location.name);

    const allMetadata = [...locationEntry.displayMetadata, ...repository.displayMetadata];

    return (
      <div ref={ref} data-index={index}>
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
              <RepositoryCountTags repo={repository} repoAddress={repoAddress} />
            </Box>
          </RowCell>
          <RowCell>
            <div>
              <LocationStatus locationStatus={locationStatus} locationOrError={locationEntry} />
            </div>
          </RowCell>
          <RowCell>
            <div style={{whiteSpace: 'nowrap'}}>
              <TimeFromNow unixTimestamp={locationStatus.updateTimestamp} />
            </div>
          </RowCell>
          <RowCell style={{alignItems: 'flex-end'}}>
            <JoinedButtons>
              <ReloadButton location={locationStatus.name} />
              <CodeLocationMenu locationNode={locationEntry} />
            </JoinedButtons>
          </RowCell>
        </RowGrid>
      </div>
    );
  },
);

export const VirtualizedCodeLocationHeader = () => {
  return (
    <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky>
      <HeaderCell>Name</HeaderCell>
      <HeaderCell>Status</HeaderCell>
      <HeaderCell>Updated</HeaderCell>
      <HeaderCell style={{textAlign: 'right'}}>Actions</HeaderCell>
    </HeaderRow>
  );
};

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
`;
