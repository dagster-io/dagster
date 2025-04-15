import {Run} from '../graphql/types';

export const isExternalRun = (run: Pick<Run, 'tags'>) => {
  return run.tags.some(
    (tag) => tag.key === 'dagster/external_job_source' && tag.value.toLowerCase() === 'airflow',
  );
};

export const getExternalRunUrl = (run: Pick<Run, 'tags'>) => {
  const airflowUrl = run.tags.find(
    (tag) => tag.key === 'dagster-airlift/airflow-dag-run-url',
  )?.value;
  if (!airflowUrl) {
    return null;
  }
  return airflowUrl;
};
