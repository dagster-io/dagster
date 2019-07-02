import * as React from "react";
import { highlightBlock } from "highlight.js";

import "highlight.js/styles/xcode.css";

export class HighlightedCodeBlock extends React.Component<{
  value: string;
  style?: React.CSSProperties;
}> {
  _el = React.createRef<HTMLPreElement>();

  componentDidMount() {
    if (this._el.current) highlightBlock(this._el.current);
  }

  render() {
    const { value, ...rest } = this.props;
    return (
      <pre ref={this._el} {...rest}>
        {value}
      </pre>
    );
  }
}
