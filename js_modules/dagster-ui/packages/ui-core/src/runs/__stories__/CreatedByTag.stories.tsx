import {MetadataTableWIP} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';

import {buildLaunchedBy, buildPipelineTag} from '../../graphql/types';
import {CreatedByTag} from '../CreatedByTag';
import {DagsterTag} from '../RunTag';
import {RunTagsFragment} from '../types/RunTagsFragment.types';
import {LaunchedByFragment} from '../types/launchedByFragment.types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'CreatedByTag',
  component: CreatedByTag,
} as Meta;

export const Default = () => {
  return (
    <MetadataTableWIP>
      <tbody>
        <tr>
          <td>User launched</td>
          <td>
            <CreatedByTag
              launchedBy={buildLaunchedBy({kind: "user", tag: buildPipelineTag({
                key: DagsterTag.User,
                value: 'foo@dagsterlabs.com',
              })}) as LaunchedByFragment}
            />
          </td>
        </tr>
        <tr>
          <td>Schedule</td>
          <td>
            <CreatedByTag
              launchedBy={buildLaunchedBy({kind: "schedule", tag: buildPipelineTag({
                key: DagsterTag.ScheduleName,
                value: 'my_cool_schedule',
              })}) as LaunchedByFragment}
            />
          </td>
        </tr>
        <tr>
          <td>Sensor</td>
          <td>
            <CreatedByTag
              launchedBy={buildLaunchedBy({kind: "sensor", tag: buildPipelineTag({
                key: DagsterTag.SensorName,
                value: 'my_cool_sensor',
              })}) as LaunchedByFragment}
            />
          </td>
        </tr>
        <tr>
          <td>Auto-materialize</td>
          <td>
            <CreatedByTag
              launchedBy={buildLaunchedBy({kind: "auto-materialize", tag: buildPipelineTag({
                key: DagsterTag.Automaterialize,
                value: 'auto',
              })}) as LaunchedByFragment}
            />
          </td>
        </tr>
        <tr>
          <td>Auto-observation</td>
          <td>
            <CreatedByTag
              launchedBy={buildLaunchedBy({kind: "auto-observe", tag: buildPipelineTag({
                key: DagsterTag.AutoObserve,
                value: 'auto',
              })}) as LaunchedByFragment}
            />
          </td>
        </tr>
        <tr>
          <td>Manually launched</td>
          <td>
            <CreatedByTag launchedBy={[] as LaunchedByFragment} />
          </td>
        </tr>
      </tbody>
    </MetadataTableWIP>
  );
};
