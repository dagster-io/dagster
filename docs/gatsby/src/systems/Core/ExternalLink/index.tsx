/** @jsx jsx */
import { jsx } from "theme-ui";
import { DetailedHTMLProps, AnchorHTMLAttributes } from "react";

type ExternalLinkProps = DetailedHTMLProps<
  AnchorHTMLAttributes<HTMLAnchorElement>,
  HTMLAnchorElement
>;

export const ExternalLink: React.FC<ExternalLinkProps> = ({
  href,
  children,
  ...props
}) => {
  return (
    <a
      sx={{ display: "flex", alignItems: "center" }}
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    >
      {children}
    </a>
  );
};
