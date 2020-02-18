/** @jsx jsx */
import { jsx } from "theme-ui";
import Img from "gatsby-image";
import styleToObj from "style-to-object";
import ModalImage from "react-modal-image";

export const Image = ({ src, width = "100%", images, style, ...props }) => {
  const img = images.find(({ node }) => node.absolutePath.includes(src));
  const st = typeof style === "string" ? styleToObj(style) : style;

  return img ? (
    <ModalImage
      hideZoom
      imageBackgroundColor="transparent"
      small={img.node.childImageSharp.fluid.src}
      smallSrcSet={img.node.childImageSharp.fluid.srcSet}
      large={img.node.childImageSharp.original.src}
      sx={{ width }}
      style={st}
    />
  ) : (
    <img src={src} {...props} alt={props.alt} style={st} />
  );
};
