type RunTag = {
  key: string;
  value: string;
};

export const isExternalRun = (run: {tags: RunTag[]}) => {
  return run.tags.some(
    (tag) => tag.key === 'dagster/external_job_source' && tag.value.toLowerCase() === 'airflow',
  );
};

export const getExternalRunUrl = (run: {tags: RunTag[]}) => {
  const airflowUrl = run.tags.find(
    (tag) => tag.key === 'dagster-airlift/airflow-dag-run-url',
  )?.value;
  if (!airflowUrl) {
    return null;
  }
  return airflowUrl;
};
