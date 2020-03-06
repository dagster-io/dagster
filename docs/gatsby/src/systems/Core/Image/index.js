/** @jsx jsx */
import { jsx } from "theme-ui";
import Img from "gatsby-image";
import styleToObj from "style-to-object";
import ModalImage from "react-modal-image";

export const imgStyle = {
  border: "1px solid #333",
  "-webkit-box-shadow": "5px 5px 5px 0px rgba(0, 0, 0, 0.75)",
  "-moz-box-shadow": "5px 5px 5px 0px rgba(0, 0, 0, 0.75)",
  boxShadow: "5px 5px 5px 0px rgba(0, 0, 0, 0.75)"
};

export const Image = ({ src, width = "100%", images, style, ...props }) => {
  const img = images.find(({ node }) => node.absolutePath.includes(src));
  const st = {
    ...imgStyle,
    ...(typeof style === "string" ? styleToObj(style) : style)
  };

  if (img) {
    return (
      <ModalImage
        hideZoom
        imageBackgroundColor="transparent"
        small={img.node.childImageSharp.fluid.src}
        smallSrcSet={img.node.childImageSharp.fluid.srcSet}
        large={img.node.childImageSharp.original.src}
        sx={{ width, ...st }}
      />
    );
  } else {
    props.style = { ...imgStyle, ...props.style };
    return <img src={src} {...props} alt={props.alt} style={st} />;
  }
};
