/** @jsx jsx */
import { jsx } from "theme-ui";

// eslint-disable-next-line @typescript-eslint/ban-ts-ignore
// @ts-ignore
import logo from "./logo.png";
import { DetailedHTMLProps, ImgHTMLAttributes } from "react";

type LogoProps = DetailedHTMLProps<
  ImgHTMLAttributes<HTMLImageElement>,
  HTMLImageElement
>;

export const Logo: React.FC<LogoProps> = props => {
  return <img src={logo} {...props} sx={{ m: 0 }} />;
};
