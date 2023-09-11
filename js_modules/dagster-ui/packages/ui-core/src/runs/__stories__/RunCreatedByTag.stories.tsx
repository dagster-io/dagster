import {MetadataTableWIP} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';
import * as React from 'react';

import {buildPipelineTag} from '../../graphql/types';
import {RunCreatedByTag} from '../RunCreatedByCell';
import {DagsterTag} from '../RunTag';
import {RunTagsFragment} from '../types/RunTable.types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RunCreatedByTag',
  component: RunCreatedByTag,
} as Meta;

export const Default = () => {
  return (
    <MetadataTableWIP>
      <tbody>
        <tr>
          <td>User launched</td>
          <td>
            <RunCreatedByTag
              tags={
                [
                  buildPipelineTag({
                    key: DagsterTag.User,
                    value: 'foo@dagsterlabs.com',
                  }),
                ] as RunTagsFragment[]
              }
            />
          </td>
        </tr>
        <tr>
          <td>Schedule</td>
          <td>
            <RunCreatedByTag
              tags={
                [
                  buildPipelineTag({
                    key: DagsterTag.ScheduleName,
                    value: 'my_cool_schedule',
                  }),
                ] as RunTagsFragment[]
              }
            />
          </td>
        </tr>
        <tr>
          <td>Sensor</td>
          <td>
            <RunCreatedByTag
              tags={
                [
                  buildPipelineTag({
                    key: DagsterTag.SensorName,
                    value: 'my_cool_sensor',
                  }),
                ] as RunTagsFragment[]
              }
            />
          </td>
        </tr>
        <tr>
          <td>Auto-materialize</td>
          <td>
            <RunCreatedByTag
              tags={
                [
                  buildPipelineTag({
                    key: DagsterTag.Automaterialize,
                    value: 'auto',
                  }),
                ] as RunTagsFragment[]
              }
            />
          </td>
        </tr>
        <tr>
          <td>Auto-observation</td>
          <td>
            <RunCreatedByTag
              tags={
                [
                  buildPipelineTag({
                    key: DagsterTag.AutoObserve,
                    value: 'auto',
                  }),
                ] as RunTagsFragment[]
              }
            />
          </td>
        </tr>
        <tr>
          <td>Manually launched</td>
          <td>
            <RunCreatedByTag tags={[] as RunTagsFragment[]} />
          </td>
        </tr>
      </tbody>
    </MetadataTableWIP>
  );
};
