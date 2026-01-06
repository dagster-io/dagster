import {
  Body2,
  Box,
  Colors,
  Icon,
  NonIdealState,
  PageHeader,
  SpinnerWithText,
  Subtitle1,
  Tooltip,
} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {AutomationBulkActionMenu} from './AutomationBulkActionMenu';
import {AutomationTabs} from './AutomationTabs';
import {AutomationsTable} from './AutomationsTable';
import {useAutomations} from './useAutomations';
import {useTrackPageView} from '../app/analytics';
import {useAutoMaterializeSensorFlag} from '../assets/AutoMaterializeSensorFlag';
import {filterAutomationSelectionByQuery} from '../automation-selection/AntlrAutomationSelection';
import {AutomationSelectionInput} from '../automation-selection/input/AutomationSelectionInput';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {filterPermissionedInstigationState} from '../instigation/filterPermissionedInstigationState';
import {makeAutomationKey} from '../sensors/makeSensorKey';
import {CheckAllBox} from '../ui/CheckAllBox';

export const MergedAutomationRoot = () => {
  useTrackPageView();
  useDocumentTitle('Automation');

  const automaterializeSensorsFlagState = useAutoMaterializeSensorFlag();

  const {automations, repoBuckets, loading: workspaceLoading} = useAutomations();

  const [selection, setSelection] = useQueryPersistedState<string>({
    queryKey: 'selection',
    defaults: {selection: ''},
    behavior: 'push',
  });

  const filtered = useMemo(() => {
    return filterAutomationSelectionByQuery(automations, selection);
  }, [automations, selection]);

  const filteredBuckets = useMemo(() => {
    return repoBuckets
      .filter((bucket) => {
        return Array.from(filtered).some(
          (automation) =>
            automation.repo.name === bucket.repoAddress.name &&
            automation.repo.location === bucket.repoAddress.location,
        );
      })
      .map((bucket) => ({
        ...bucket,
        schedules: bucket.schedules.filter((schedule) => {
          return filtered.has(schedule);
        }),
        sensors: bucket.sensors.filter((sensor) => {
          return filtered.has(sensor);
        }),
      }))
      .filter((bucket) => !!bucket.schedules.length || !!bucket.sensors.length);
  }, [repoBuckets, filtered]);

  // Collect all automations across visible code locations that the viewer has permission
  // to start or stop.
  const allPermissionedAutomations = useMemo(() => {
    return filteredBuckets
      .map(({repoAddress, schedules, sensors}) => {
        return [
          ...sensors
            .filter(({sensorState}) => filterPermissionedInstigationState(sensorState))
            .map(({name, sensorState}) => ({
              repoAddress,
              name,
              type: 'sensor' as const,
              instigationState: sensorState,
            })),
          ...schedules
            .filter(({scheduleState}) => filterPermissionedInstigationState(scheduleState))
            .map(({name, scheduleState}) => ({
              repoAddress,
              name,
              type: 'schedule' as const,
              instigationState: scheduleState,
            })),
        ];
      })
      .flat();
  }, [filteredBuckets]);

  // Build a list of keys from the permissioned schedules for use in checkbox state.
  // This includes collapsed code locations.
  const allPermissionedAutomationKeys = useMemo(() => {
    return allPermissionedAutomations.map(({repoAddress, name}) =>
      makeAutomationKey(repoAddress, name),
    );
  }, [allPermissionedAutomations]);

  const [{checkedIds: checkedKeys}, {onToggleFactory, onToggleAll}] = useSelectionReducer(
    allPermissionedAutomationKeys,
  );

  // Filter to find keys that are visible given any text search.
  const permissionedKeysOnScreen = useMemo(() => {
    const filteredKeys = new Set(
      filteredBuckets
        .map(({repoAddress, schedules, sensors}) => {
          return [...schedules, ...sensors].map(({name}) => makeAutomationKey(repoAddress, name));
        })
        .flat(),
    );
    return allPermissionedAutomationKeys.filter((key) => filteredKeys.has(key));
  }, [allPermissionedAutomationKeys, filteredBuckets]);

  // Determine the list of sensor objects that have been checked by the viewer.
  // These are the sensors that will be operated on by the bulk start/stop action.
  const checkedAutomations = useMemo(() => {
    const checkedKeysOnScreen = new Set(
      permissionedKeysOnScreen.filter((key: string) => checkedKeys.has(key)),
    );
    return allPermissionedAutomations.filter(({repoAddress, name}) => {
      return checkedKeysOnScreen.has(makeAutomationKey(repoAddress, name));
    });
  }, [permissionedKeysOnScreen, allPermissionedAutomations, checkedKeys]);

  const viewerHasAnyInstigationPermission = allPermissionedAutomationKeys.length > 0;
  const checkedCount = checkedAutomations.length;
  const anyAutomationsVisible = permissionedKeysOnScreen.length > 0;

  const repos = useMemo(() => {
    return filteredBuckets.map((bucket) => ({
      repoAddress: bucket.repoAddress,
      schedules: bucket.schedules.map((schedule) => schedule.name),
      sensors: bucket.sensors.map((sensor) => sensor.name),
    }));
  }, [filteredBuckets]);

  const content = () => {
    if (workspaceLoading) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} padding={{top: 64}}>
          <SpinnerWithText label="Loading automations…" />
        </Box>
      );
    }

    if (filteredBuckets.length === 0) {
      if (selection) {
        return (
          <Box padding={{top: 20}}>
            <NonIdealState
              icon="search"
              title="No matching automations"
              description={
                <div>
                  No automations matching <strong>{selection}</strong> were found in your
                  definitions
                </div>
              }
            />
          </Box>
        );
      }

      return (
        <Box padding={{top: 20}}>
          <NonIdealState
            icon="search"
            title="No automations"
            description={
              <Body2>
                There are no automations in this deployment.{' '}
                <a
                  href="https://docs.dagster.io/concepts/automation"
                  target="_blank"
                  rel="noreferrer"
                >
                  <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                    Learn more about automations
                    <Icon name="open_in_new" color={Colors.linkDefault()} />
                  </Box>
                </a>
              </Body2>
            }
          />
        </Box>
      );
    }

    return (
      <AutomationsTable
        headerCheckbox={
          viewerHasAnyInstigationPermission ? (
            <CheckAllBox
              checkedCount={checkedCount}
              totalCount={permissionedKeysOnScreen.length}
              onToggleAll={onToggleAll}
            />
          ) : undefined
        }
        repos={repos}
        checkedKeys={checkedKeys}
        onToggleCheckFactory={onToggleFactory}
      />
    );
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader title={<Subtitle1>Automation</Subtitle1>} />
      {automaterializeSensorsFlagState === 'has-global-amp' ? (
        <Box padding={{horizontal: 24}} border="bottom">
          <AutomationTabs tab="schedules-and-sensors" />
        </Box>
      ) : null}
      <Box
        padding={{horizontal: 24, vertical: 12}}
        flex={{
          direction: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          grow: 0,
        }}
      >
        <Box flex={{grow: 1}}>
          <AutomationSelectionInput items={automations} value={selection} onChange={setSelection} />
        </Box>
        <Tooltip
          content="You do not have permission to start or stop these schedules"
          canShow={anyAutomationsVisible && !viewerHasAnyInstigationPermission}
          placement="top-end"
        >
          <AutomationBulkActionMenu automations={checkedAutomations} />
        </Tooltip>
      </Box>
      {content()}
    </Box>
  );
};

// eslint-disable-next-line import/no-default-export
export default MergedAutomationRoot;
