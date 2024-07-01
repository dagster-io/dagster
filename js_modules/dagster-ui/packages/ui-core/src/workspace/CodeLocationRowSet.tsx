import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Icon,
  MiddleTruncate,
  Tag,
  Tooltip,
} from '@dagster-io/ui-components';
import {useCallback, useMemo, useState} from 'react';
import styled from 'styled-components';

import {RepositoryLocationNonBlockingErrorDialog} from './RepositoryLocationErrorDialog';
import {WorkspaceRepositoryLocationNode} from './WorkspaceContext';
import {
  LocationStatusEntryFragment,
  WorkspaceDisplayMetadataFragment,
} from './types/WorkspaceQueries.types';
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

export const ImageName = ({metadata}: {metadata: WorkspaceDisplayMetadataFragment[]}) => {
  const copy = useCopyToClipboard();
  const imageKV = metadata.find(({key}) => key === 'image');
  const value = imageKV?.value || '';

  const onClick = useCallback(async () => {
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
  locationStatus: LocationStatusEntryFragment;
  locationOrError: WorkspaceRepositoryLocationNode | null;
}) => {
  const {locationStatus, locationOrError} = props;
  const [showDialog, setShowDialog] = useState(false);

  const reloadFn = useMemo(
    () => buildReloadFnForLocation(locationStatus.name),
    [locationStatus.name],
  );
  const {reloading, tryReload} = useRepositoryLocationReload({
    scope: 'location',
    reloadFn,
  });

  if (locationStatus.loadStatus === 'LOADING') {
    return (
      <Tag minimal intent="primary">
        Updating...
      </Tag>
    );
  }

  if (locationOrError?.updatedTimestamp !== locationStatus.updateTimestamp) {
    return (
      <Tag minimal intent="primary">
        Loading...
      </Tag>
    );
  }

  if (locationOrError?.locationOrLoadError?.__typename === 'PythonError') {
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
          location={locationStatus.name}
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
