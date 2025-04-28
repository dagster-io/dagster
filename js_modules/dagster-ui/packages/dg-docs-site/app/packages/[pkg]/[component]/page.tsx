import getContents, {getComponent} from '@/util/getContents';
import ComponentPageContents from '@dagster-io/dg-docs-components/ComponentPageContents';

interface Props {
  params: Promise<{pkg: string; component: string}>;
}

export default async function ComponentPage({params}: Props) {
  const {pkg, component} = await params;
  const contents = await getContents();
  if (!contents) {
    return <div>Contents not found</div>;
  }

  const componentConfig = await getComponent(contents, pkg, component);
  if (!componentConfig) {
    return <div>Component not found</div>;
  }

  return <ComponentPageContents componentConfig={componentConfig} />;
}

export async function generateStaticParams() {
  const contents = await getContents();
  if (!contents) {
    return [];
  }
  return contents
    .map((pkg) => {
      return pkg.componentTypes.map(({name}) => ({
        pkg: pkg.name,
        component: name,
      }));
    })
    .flat();
}
