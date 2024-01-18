import * as React from 'react';
import {Meta} from '@storybook/react';

import {MetadataTableWIP} from '@dagster-io/ui-components';

import {buildPipelineTag} from '../../graphql/types';
import {CreatedByTag} from '../CreatedByTag';
import {DagsterTag} from '../RunTag';
import {RunTagsFragment} from '../types/RunTable.types';

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
            <CreatedByTag
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
            <CreatedByTag
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
            <CreatedByTag
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
            <CreatedByTag
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
            <CreatedByTag tags={[] as RunTagsFragment[]} />
          </td>
        </tr>
      </tbody>
    </MetadataTableWIP>
  );
};
