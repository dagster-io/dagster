import PackageTreeSync from './PackageTreeSync';
import getContents from '../../util/getContents';

export default async function PackageTree() {
  const contents = await getContents();
  return <PackageTreeSync contents={contents} />;
}
