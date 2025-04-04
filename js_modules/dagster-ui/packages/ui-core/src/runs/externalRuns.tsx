import {Run} from '../graphql/types';

export const isExternalRun = (run: Pick<Run, 'tags'>) => {
  return run.tags.some((tag) => tag.key === 'dagster/external_job' && tag.value === 'airflow');
};

export const getExternalRunUrl = (run: Pick<Run, 'tags'>) => {
  const airflowId = run.tags.find((tag) => tag.key === 'dagster/airflow_id')?.value;
  if (!airflowId) {
    return null;
  }
  // TODO: figure out external URL for airflow
  return `/airflow/run/${airflowId}`;
};
