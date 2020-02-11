/** @jsx jsx */
import { jsx } from "theme-ui";
import Img from "gatsby-image";
import styleToObj from "style-to-object";

export const Image = ({ src, width = "100%", images, style, ...props }) => {
  const img = images.find(({ node }) => node.absolutePath.includes(src));
  const st = typeof style === "string" ? styleToObj(style) : style;
  return img ? (
    <Img
      {...props}
      fluid={img.node.childImageSharp.fluid}
      sx={{ width }}
      style={st}
    />
  ) : (
    <img src={src} {...props} alt={props.alt} style={st} />
  );
};
