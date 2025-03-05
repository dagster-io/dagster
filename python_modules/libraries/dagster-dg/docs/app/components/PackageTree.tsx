import {Contents} from '@/util/types';

import getContents from '@/util/getContents';
import {Suspense} from 'react';
import PackageTreeInner from '@/app/components/PackageTreeInner';

interface Props {
  contents: Contents | null;
}

export default function PackageTree({contents}: Props) {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <PackageTreeInner contents={contents} />
    </Suspense>
  );
}

export async function getStaticProps() {
  const contents = await getContents();
  return {
    props: {contents},
  };
}
