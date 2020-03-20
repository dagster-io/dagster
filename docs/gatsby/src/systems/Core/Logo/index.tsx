/** @jsx jsx */
import { jsx } from "theme-ui";

// eslint-disable-next-line @typescript-eslint/ban-ts-ignore
// @ts-ignore
import logo from "./logo.png";

type LogoProps = JSX.IntrinsicElements["img"];

export const Logo: React.FC<LogoProps> = props => {
  return <img src={logo} {...props} sx={{ m: 0 }} />;
};
