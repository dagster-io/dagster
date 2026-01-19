import {ProductTour, ProductTourPosition} from '@dagster-io/ui-components';

import ShowAndHideTagsMP4 from './ShowAndHideRunTags.mp4';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

export function RunTableTargetHeader() {
  const [hideTabPinningNux, setHideTabPinningNux] = useStateWithStorage<any>(
    'RunTableTabPinningNux',
    (value) => value,
  );
  if (hideTabPinningNux) {
    return <div>目标</div>;
  }
  return (
    <ProductTour
      title="显示/隐藏运行标签"
      description={
        <>
          您可以通过将鼠标悬停在标签上并选择显示/隐藏选项来快速访问或隐藏特定标签。
        </>
      }
      position={ProductTourPosition.BOTTOM_RIGHT}
      video={ShowAndHideTagsMP4}
      width="616px"
      actions={{
        dismiss: () => {
          setHideTabPinningNux('1');
        },
      }}
    >
      <div>目标</div>
    </ProductTour>
  );
}
