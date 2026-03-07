import ComponentTags from '@dagster-io/dg-docs-components/ComponentTags';

export const DGDocs = () => {
  const tags = ['component', 'documentation'];
  const owners = ['foo@bar.com'];
  return (
    <div>
      <ComponentTags owners={owners} tags={tags} />
    </div>
  );
};
