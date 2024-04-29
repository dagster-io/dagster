import {getColorForString} from '../../util/getColorForString';

export const Badge = ({text}) => {
  const colors = getColorForString(text);
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-sm font-medium ${colors}`}
    >
      {text}
    </span>
  );
};
