import {ProductTour, ProductTourPosition} from '@dagster-io/ui-components';

import ShowAndHideTagsMP4 from './ShowAndHideRunTags.mp4';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

export function RunTableTargetHeader() {
  const [hideTabPinningNux, setHideTabPinningNux] = useStateWithStorage<any>(
    'RunTableTabPinningNux',
    (value) => value,
  );
  if (hideTabPinningNux) {
    return <div>Target</div>;
  }
  return (
    <ProductTour
      title="Hide and show run tags"
      description={
        <>
          You can show tags that you prefer quick access to and hide tags you don&apos;t by hovering
          over the tag and selecting the show/hide tag option.
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
      <div>Target</div>
    </ProductTour>
  );
}
