import getContents from '../util/getContents';
import ListView from '@dagster-io/dg-docs-components/ListView';
import Link from 'next/link';

export default async function Home() {
  const contents = await getContents();

  return (
    <ListView
      loading={false}
      contents={contents}
      renderLink={({key, href, children, ...rest}) => {
        return (
          <Link key={key} href={href || '#'} {...rest}>
            {children}
          </Link>
        );
      }}
    />
  );
}
