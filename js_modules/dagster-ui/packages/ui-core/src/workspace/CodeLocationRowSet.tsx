import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Icon,
  JoinedButtons,
  MiddleTruncate,
  Tag,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {CodeLocationMenu} from './CodeLocationMenu';
import {RepositoryCountTags} from './RepositoryCountTags';
import {RepositoryLocationNonBlockingErrorDialog} from './RepositoryLocationErrorDialog';
import {WorkspaceRepositoryLocationNode} from './WorkspaceContext';
import {buildRepoAddress} from './buildRepoAddress';
import {repoAddressAsHumanString} from './repoAddressAsString';
import {WorkspaceDisplayMetadataFragment} from './types/WorkspaceContext.types';
import {workspacePathFromAddress} from './workspacePath';
import {showSharedToaster} from '../app/DomUtils';
import {useCopyToClipboard} from '../app/browser';
import {
  NO_RELOAD_PERMISSION_TEXT,
  ReloadRepositoryLocationButton,
} from '../nav/ReloadRepositoryLocationButton';
import {
  buildReloadFnForLocation,
  useRepositoryLocationReload,
} from '../nav/useRepositoryLocationReload';
import {TimeFromNow} from '../ui/TimeFromNow';

interface Props {
  locationNode: WorkspaceRepositoryLocationNode;
}

export const CodeLocationRowSet = ({locationNode}: Props) => {
  const {name, locationOrLoadError} = locationNode;

  if (!locationOrLoadError || locationOrLoadError?.__typename === 'PythonError') {
    return (
      <tr>
        <td style={{maxWidth: '400px', color: Colors.textLight()}}>
          <MiddleTruncate text={name} />
        </td>
        <td>
          <LocationStatus location={name} locationOrError={locationNode} />
        </td>
        <td style={{whiteSpace: 'nowrap'}}>
          <TimeFromNow unixTimestamp={locationNode.updatedTimestamp} />
        </td>
        <td>{'\u2013'}</td>
        <td style={{width: '180px'}}>
          <JoinedButtons>
            <ReloadButton location={name} />
            <CodeLocationMenu locationNode={locationNode} />
          </JoinedButtons>
        </td>
      </tr>
    );
  }

  const repositories = [...locationOrLoadError.repositories].sort((a, b) =>
    a.name.localeCompare(b.name),
  );

  return (
    <>
      {repositories.map((repository) => {
        const repoAddress = buildRepoAddress(repository.name, name);
        const allMetadata = [...locationNode.displayMetadata, ...repository.displayMetadata];
        return (
          <tr key={repoAddressAsHumanString(repoAddress)}>
            <td style={{maxWidth: '400px'}}>
              <Box flex={{direction: 'column', gap: 4}}>
                <div style={{fontWeight: 500}}>
                  <Link to={workspacePathFromAddress(repoAddress)}>
                    <MiddleTruncate text={repoAddressAsHumanString(repoAddress)} />
                  </Link>
                </div>
                <ImageName metadata={allMetadata} />
                <ModuleOrPackageOrFile metadata={allMetadata} />
              </Box>
            </td>
            <td>
              <LocationStatus location={repository.name} locationOrError={locationNode} />
            </td>
            <td style={{whiteSpace: 'nowrap'}}>
              <TimeFromNow unixTimestamp={locationNode.updatedTimestamp} />
            </td>
            <td>
              <RepositoryCountTags repo={repository} repoAddress={repoAddress} />
            </td>
            <td style={{width: '180px'}}>
              <JoinedButtons>
                <ReloadButton location={name} />
                <CodeLocationMenu locationNode={locationNode} />
              </JoinedButtons>
            </td>
          </tr>
        );
      })}
    </>
  );
};

export const ImageName = ({metadata}: {metadata: WorkspaceDisplayMetadataFragment[]}) => {
  const copy = useCopyToClipboard();
  const imageKV = metadata.find(({key}) => key === 'image');
  const value = imageKV?.value || '';

  const onClick = React.useCallback(async () => {
    copy(value);
    await showSharedToaster({
      intent: 'success',
      icon: 'done',
      message: 'Image string copied!',
    });
  }, [copy, value]);

  if (imageKV) {
    return (
      <ImageNameBox flex={{direction: 'row', gap: 4}}>
        <span style={{fontWeight: 500}}>image:</span>
        <Tooltip content="Click to copy" placement="top" display="block">
          <button onClick={onClick}>
            <MiddleTruncate text={imageKV.value} />
          </button>
        </Tooltip>
      </ImageNameBox>
    );
  }
  return null;
};

const ImageNameBox = styled(Box)`
  width: 100%;
  color: ${Colors.textLight()};
  font-size: 12px;

  .bp4-popover2-target {
    overflow: hidden;
  }

  button {
    background: ${Colors.backgroundDefault()};
    border: none;
    color: ${Colors.textLight()};
    cursor: pointer;
    font-size: 12px;
    overflow: hidden;
    padding: 0;
    margin: 0;
    width: 100%;

    :focus {
      outline: none;
    }
  }
`;

export const ModuleOrPackageOrFile = ({
  metadata,
}: {
  metadata: WorkspaceDisplayMetadataFragment[];
}) => {
  const imageKV = metadata.find(
    ({key}) => key === 'module_name' || key === 'package_name' || key === 'python_file',
  );
  if (imageKV) {
    return (
      <Box
        flex={{direction: 'row', gap: 4}}
        style={{width: '100%', color: Colors.textLight(), fontSize: 12}}
      >
        <span style={{fontWeight: 500}}>{imageKV.key}:</span>
        <MiddleTruncate text={imageKV.value} />
      </Box>
    );
  }
  return null;
};

export const LocationStatus = (props: {
  location: string;
  locationOrError: WorkspaceRepositoryLocationNode;
}) => {
  const {location, locationOrError} = props;
  const [showDialog, setShowDialog] = React.useState(false);

  const reloadFn = React.useMemo(() => buildReloadFnForLocation(location), [location]);
  const {reloading, tryReload} = useRepositoryLocationReload({
    scope: 'location',
    reloadFn,
  });

  if (locationOrError.loadStatus === 'LOADING') {
    if (locationOrError.locationOrLoadError) {
      return (
        <Tag minimal intent="primary">
          Updating...
        </Tag>
      );
    } else {
      return (
        <Tag minimal intent="primary">
          Loading...
        </Tag>
      );
    }
  }

  if (locationOrError.locationOrLoadError?.__typename === 'PythonError') {
    return (
      <>
        <Box flex={{alignItems: 'center', gap: 12}}>
          <Tag minimal intent="danger">
            Failed
          </Tag>
          <ButtonLink onClick={() => setShowDialog(true)}>
            <span style={{fontSize: '14px'}}>View error</span>
          </ButtonLink>
        </Box>
        <RepositoryLocationNonBlockingErrorDialog
          location={location}
          isOpen={showDialog}
          error={locationOrError.locationOrLoadError}
          reloading={reloading}
          onDismiss={() => setShowDialog(false)}
          onTryReload={() => tryReload()}
        />
      </>
    );
  }

  return (
    <Tag minimal intent="success">
      Loaded
    </Tag>
  );
};

export const ReloadButton = ({location}: {location: string}) => {
  return (
    <ReloadRepositoryLocationButton
      location={location}
      ChildComponent={({reloading, tryReload, hasReloadPermission}) => {
        return (
          <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
            <Tooltip
              content={hasReloadPermission ? '' : NO_RELOAD_PERMISSION_TEXT}
              canShow={!hasReloadPermission}
              useDisabledButtonTooltipFix
            >
              <Button
                icon={<Icon name="refresh" />}
                disabled={!hasReloadPermission}
                loading={reloading}
                onClick={() => tryReload()}
              >
                Reload
              </Button>
            </Tooltip>
          </Box>
        );
      }}
    />
  );
};
