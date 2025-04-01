import ComponentTags from '@dagster-io/dg-docs-components/ComponentTags';

export const DGDocs = () => {
  const tags = ['component', 'documentation'];
  return (
    <div>
      <ComponentTags author="foo@bar.com" tags={tags} />
    </div>
  );
};
