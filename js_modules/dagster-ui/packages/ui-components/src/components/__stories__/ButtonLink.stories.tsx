import {ButtonLink} from '../ButtonLink';
import {Colors} from '../Color';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'ButtonLink',
  component: ButtonLink,
};

export const ColorString = () => {
  return <ButtonLink color={Colors.linkDefault()}>Hello world</ButtonLink>;
};

export const ColorMap = () => {
  return (
    <ButtonLink
      color={{
        link: Colors.linkDefault(),
        hover: Colors.linkHover(),
        active: Colors.accentGreen(),
      }}
    >
      Hello world
    </ButtonLink>
  );
};

export const HoverUnderline = () => {
  return (
    <ButtonLink color={Colors.linkDefault()} underline="hover">
      Hello world
    </ButtonLink>
  );
};

export const WithinText = () => {
  return (
    <div>
      Lorem ipsum{' '}
      <ButtonLink
        color={{link: Colors.linkDefault(), hover: Colors.linkHover()}}
        underline="always"
      >
        dolor sit
      </ButtonLink>{' '}
      amet edipiscing.
    </div>
  );
};
