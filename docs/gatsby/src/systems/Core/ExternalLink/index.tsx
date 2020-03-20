/** @jsx jsx */
import { jsx } from "theme-ui";

type ExternalLinkProps = JSX.IntrinsicElements["a"];

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
