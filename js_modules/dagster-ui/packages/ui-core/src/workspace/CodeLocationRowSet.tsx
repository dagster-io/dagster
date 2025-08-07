import {
  Box,
  Button,
  ButtonLink,
  CaptionMono,
  Colors,
  FontFamily,
  Icon,
  MiddleTruncate,
  Tag,
  Tooltip,
  UnstyledButton,
} from '@dagster-io/ui-components';
import {useCallback, useMemo, useState} from 'react';
import styled from 'styled-components';

import {RepositoryLocationNonBlockingErrorDialog} from './RepositoryLocationErrorDialog';
import {WorkspaceRepositoryLocationNode} from './WorkspaceContext/WorkspaceContext';
import {useCopyToClipboard} from '../app/browser';
import {useLatestStateVersions} from '../code-location/useLatestStateVersions';
import {
  NO_RELOAD_PERMISSION_TEXT,
  ReloadRepositoryLocationButton,
} from '../nav/ReloadRepositoryLocationButton';
import {
  buildReloadFnForLocation,
  useRepositoryLocationReload,
} from '../nav/useRepositoryLocationReload';
import {
  LocationStatusEntryFragment,
  WorkspaceDisplayMetadataFragment,
} from './WorkspaceContext/types/WorkspaceQueries.types';

export const ImageName = ({metadata}: {metadata: WorkspaceDisplayMetadataFragment[]}) => {
  const copy = useCopyToClipboard();
  const [didCopy, setDidCopy] = useState(false);
  const imageKV = metadata.find(({key}) => key === 'image');
  const value = imageKV?.value || '';

  const onClick = useCallback(async () => {
    copy(value);
    setDidCopy(true);
    const timer = setTimeout(() => {
      setDidCopy(false);
    }, 3000);
    return () => clearTimeout(timer);
  }, [copy, value]);

  if (imageKV) {
    return (
      <ImageNameBox>
        <span style={{fontWeight: 500}}>image: </span>
        <span style={{marginRight: '4px'}}>
          <CaptionMono>{imageKV.value}</CaptionMono>
        </span>
        <Tooltip content={didCopy ? 'Copied!' : 'Click to copy image string'} placement="top">
          <UnstyledButton onClick={onClick}>
            <Icon name={didCopy ? 'done' : 'copy'} size={12} />
          </UnstyledButton>
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

  .bp5-popover-target {
    display: inline;
    overflow: hidden;
    position: relative;
    top: 1px;
  }
`;

export const ModuleOrPackageOrFile = ({
  metadata,
}: {
  metadata: WorkspaceDisplayMetadataFragment[];
}) => {
  const imageKV = metadata.find(
    ({key}) =>
      key === 'module_name' ||
      key === 'package_name' ||
      key === 'python_file' ||
      key === 'autoload_defs_module_name',
  );
  if (imageKV) {
    return (
      <Box
        flex={{direction: 'row', gap: 4}}
        style={{width: '100%', color: Colors.textLight(), fontSize: 12}}
      >
        <span style={{fontWeight: 500}}>{imageKV.key}:</span>
        <div style={MetadataValueButtonStyle}>
          <MiddleTruncate text={imageKV.value} />
        </div>
      </Box>
    );
  }
  return null;
};

export const LocationStatus = (props: {
  locationStatus: LocationStatusEntryFragment | null;
  locationOrError: WorkspaceRepositoryLocationNode | null;
}) => {
  const {locationStatus, locationOrError} = props;
  const [showDialog, setShowDialog] = useState(false);
  const {latestStateVersions} = useLatestStateVersions();

  const reloadFn = useMemo(
    () => buildReloadFnForLocation(locationStatus?.name || ''),
    [locationStatus?.name],
  );
  const {reloading, tryReload} = useRepositoryLocationReload({
    scope: 'location',
    reloadFn,
  });

  const hasOutdatedStateVersions = useMemo(() => {
    if (!locationOrError?.stateVersions?.versionInfo || !latestStateVersions) {
      return false;
    }

    const currentVersions = locationOrError.stateVersions.versionInfo;
    const latestVersionsMap = new Map(latestStateVersions.map((info) => [info.name, info.version]));

    return currentVersions.some((currentInfo) => {
      const latestVersion = latestVersionsMap.get(currentInfo.name);
      return latestVersion && currentInfo.version !== latestVersion;
    });
  }, [locationOrError?.stateVersions?.versionInfo, latestStateVersions]);

  if (locationStatus?.loadStatus === 'LOADING') {
    return (
      <Tag minimal intent="primary">
        Updating…
      </Tag>
    );
  }

  if (locationOrError?.versionKey !== locationStatus?.versionKey) {
    return (
      <Tag minimal intent="primary">
        Loading…
      </Tag>
    );
  }

  if (locationStatus && locationOrError?.locationOrLoadError?.__typename === 'PythonError') {
    return (
      <>
        <Box flex={{alignItems: 'center', gap: 12}}>
          <Tag minimal intent="danger">
            Failed
          </Tag>
          <ButtonLink onClick={() => setShowDialog(true)}>
            <span style={{fontSize: '12px'}}>View error</span>
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
    <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
      <Tag minimal intent="success">
        Loaded
      </Tag>
      {hasOutdatedStateVersions && (
        <Tooltip content="State versions are outdated" placement="top">
          <Icon name="warning" color={Colors.accentYellow()} size={16} />
        </Tooltip>
      )}
    </Box>
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
                icon={<Icon name="code_location_reload" />}
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

const MetadataValueButtonStyle = {
  width: '100%',
  display: 'block',
  fontFamily: FontFamily.monospace,
  fontSize: '12px',
  color: Colors.textLight(),
};
