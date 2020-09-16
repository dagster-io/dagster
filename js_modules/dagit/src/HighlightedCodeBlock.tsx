import {configure, highlightBlock} from 'highlight.js';
import * as React from 'react';

import 'highlight.js/styles/xcode.css';

export class HighlightedCodeBlock extends React.Component<{
  value: string;
  languages: string[];
  style?: React.CSSProperties;
}> {
  _el = React.createRef<HTMLPreElement>();

  componentDidMount() {
    if (this._el.current) {
      configure({languages: this.props.languages});
      highlightBlock(this._el.current);
    }
  }

  render() {
    const {value, ...rest} = this.props;
    return (
      <pre ref={this._el} {...rest}>
        {value}
      </pre>
    );
  }
}
