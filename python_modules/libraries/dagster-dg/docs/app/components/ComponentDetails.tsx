import {ComponentType} from "@/util/types";

import ComponentHeader from "@/app/components/ComponentHeader";

interface Props {
  config: ComponentType;
}

export default function ComponentDetails({config}: Props) {
  return (
    <div>
      <ComponentHeader config={config} />
    </div>
  );
}
