import getContents from '@/util/getContents';
import PackageTreeInner from '@/app/components/PackageTreeInner';

export default async function PackageTree() {
  const contents = await getContents();
  return <PackageTreeInner contents={contents} />;
}
