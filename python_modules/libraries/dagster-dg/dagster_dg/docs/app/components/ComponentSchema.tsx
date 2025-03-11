import styles from './css/ComponentSchema.module.css';

interface Props {
  schema: string;
}

export default function ComponentSchema({schema}: Props) {
  let json;
  try {
    json = JSON.parse(schema);
  } catch (error) {
    console.error(error);
  }

  if (!json) {
    return <div className={styles.container}>Invalid schema</div>;
  }

  return (
    <div className={styles.container}>
      <pre>{JSON.stringify(json, null, 2)}</pre>
    </div>
  );
}
