import {
  Button,
  Classes,
  Colors,
  Dialog,
  IBreadcrumbProps,
  NonIdealState,
  Spinner,
  Tag,
} from '@blueprintjs/core';
import React from 'react';
import styled from 'styled-components';

import {ButtonLink} from 'src/ButtonLink';
import {LoadingCentering, LoadingContainer, LoadingWithProgress} from 'src/Loading';
import {useRepositoryLocationReload} from 'src/nav/ReloadRepositoryLocationButton';
import {TopNav} from 'src/nav/TopNav';
import {Page} from 'src/ui/Page';
import {Table} from 'src/ui/Table';
import {FontFamily} from 'src/ui/styles';
import {RepositoryLocationQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes as LocationOrError} from 'src/workspace/types/RepositoryLocationQuery';
import {useRepositoryLocations} from 'src/workspace/useRepositoryLocations';

const LocationStatus: React.FC<{locationOrError: LocationOrError; reloading: boolean}> = (
  props,
) => {
  const {locationOrError, reloading} = props;
  const [showDialog, setShowDialog] = React.useState(false);

  if (reloading) {
    return (
      <Tag minimal intent="primary">
        Reloading...
      </Tag>
    );
  }

  if (locationOrError.__typename === 'RepositoryLocationLoadFailure') {
    return (
      <>
        <div style={{display: 'flex', alignItems: 'start'}}>
          <Tag minimal intent="danger">
            Failed
          </Tag>
          <div style={{fontSize: '14px', marginLeft: '8px'}}>
            <SmallButtonLink onClick={() => setShowDialog(true)}>View error</SmallButtonLink>
          </div>
        </div>
        <Dialog
          isOpen={showDialog}
          title="Repository location error"
          onClose={() => setShowDialog(false)}
          style={{width: '700px'}}
        >
          <div className={Classes.DIALOG_BODY}>
            <div style={{marginBottom: '12px'}}>
              Error loading <strong>{locationOrError.name}</strong>. Try reloading the repository
              location after resolving the issue.
            </div>
            <Trace>{locationOrError.error.message}</Trace>
          </div>
          <div className={Classes.DIALOG_FOOTER}>
            <div className={Classes.DIALOG_FOOTER_ACTIONS}>
              <Button onClick={() => setShowDialog(false)}>OK</Button>
            </div>
          </div>
        </Dialog>
      </>
    );
  }
  return (
    <Tag minimal intent="success">
      Loaded
    </Tag>
  );
};

const ReloadButton: React.FC<{location: string; onReload: (location: string) => Promise<any>}> = (
  props,
) => {
  const {location, onReload} = props;
  const {reloading, onClick} = useRepositoryLocationReload(location, () => onReload(location));
  return (
    <SmallButtonLink onClick={onClick}>
      <div style={{display: 'flex', alignItems: 'center'}}>
        Reload
        {reloading ? (
          <div style={{marginLeft: '4px'}}>
            <Spinner size={12} />
          </div>
        ) : null}
      </div>
    </SmallButtonLink>
  );
};

export const WorkspaceRepositoryLocationsRoot: React.FC<{}> = () => {
  const {nodes, loading, refetch} = useRepositoryLocations();
  const [reloading, setReloading] = React.useState<string | null>(null);

  if (loading && !nodes.length) {
    return <LoadingWithProgress />;
  }

  if (!nodes.length) {
    return (
      <LoadingContainer>
        <LoadingCentering>
          <NonIdealState icon="cube" title="No repository locations!" />
        </LoadingCentering>
      </LoadingContainer>
    );
  }

  const breadcrumbs: IBreadcrumbProps[] = [
    {text: 'Workspace', icon: 'cube'},
    {text: 'Repository locations'},
  ];

  const onReload = async (name: string) => {
    setReloading(name);
    await refetch();
    setReloading(null);
  };

  return (
    <>
      <TopNav breadcrumbs={breadcrumbs} />
      <Page>
        <Table striped style={{width: '100%'}}>
          <thead>
            <tr>
              <th>Repository location</th>
              <th colSpan={2}>Status</th>
            </tr>
          </thead>
          <tbody>
            {nodes.map((node) => (
              <tr key={node.name}>
                <td style={{width: '30%'}}>{node.name}</td>
                <td style={{width: '20%'}}>
                  <LocationStatus locationOrError={node} reloading={node.name === reloading} />
                </td>
                <td style={{width: '100%'}}>
                  <ReloadButton location={node.name} onReload={onReload} />
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Page>
    </>
  );
};

const Trace = styled.div`
  background-color: ${Colors.LIGHT_GRAY1};
  color: rgb(41, 50, 56);
  font-family: ${FontFamily.monospace};
  font-size: 12px;
  max-height: 60vh;
  overflow: auto;
  white-space: pre;
  padding: 16px;
`;

const SmallButtonLink = styled(ButtonLink)`
  font-size: 14px;
  margin: 0;
  padding: 0;

  &:active,
  :focus {
    outline: none;
  }
`;
