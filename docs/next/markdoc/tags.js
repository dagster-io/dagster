import {ArticleList, ArticleListItem} from '../components/markdoc/ArticleList';
import {Badge, Experimental, Preview, Beta, Deprecated, Superseded, Legacy} from '../components/markdoc/Badges';
import {Button, ButtonContainer} from '../components/markdoc/Button';
import {Note, Warning} from '../components/markdoc/Callouts';
import {Check, Cross} from '../components/markdoc/CheckCross';
import {CodeReferenceLink} from '../components/markdoc/CodeReferenceLink';
import {CodeSnippet} from '../components/markdoc/CodeSnippet';
import {MyImage} from '../components/markdoc/Image';
import {ReferenceTable, ReferenceTableItem} from '../components/markdoc/ReferenceTable';

export const note = {
  render: Note,
};

export const warning = {
  render: Warning,
};

export const buttonContainer = {
  render: ButtonContainer,
};

export const button = {
  render: Button,
  children: ['text'],
  attributes: {
    link: {
      type: String,
    },
    style: {
      type: String,
      default: 'primary',
      matches: ['primary', 'secondary', 'blurple'],
    },
  },
};

export const check = {
  render: Check,
  selfClosing: true,
};

export const cross = {
  render: Cross,
  selfClosing: true,
};

export const image = {
  render: MyImage,
  selfClosing: true,
  attributes: {
    src: {
      type: String,
    },
    alt: {
      type: String,
    },
    width: {
      type: Number,
    },
    height: {
      type: Number,
    },
  },
};

export const badge = {
  render: Badge,
  selfClosing: true,
  children: ['text'],
  attributes: {
    text: {
      type: String,
    },
  },
};

export const experimental = {
  render: Experimental,
  selfClosing: true,
};

export const preview = {
  render: Preview,
  selfClosing: true,
};

export const beta = {
  render: Beta,
  selfClosing: true,
};

export const deprecated = {
  render: Deprecated,
  selfClosing: true,
};

export const superseded = {
  render: Superseded,
  selfClosing: true,
};

export const legacy = {
  render: Legacy,
  selfClosing: true,
};

export const codeReferenceLink = {
  render: CodeReferenceLink,
  children: ['text'],
  attributes: {
    filePath: {
      type: String,
    },
    isInline: {
      type: Boolean,
      default: false,
    },
  },
};

export const referenceTable = {
  render: ReferenceTable,
};

export const referenceTableItem = {
  render: ReferenceTableItem,
  attributes: {
    propertyName: {
      type: String,
    },
  },
};

export const articleList = {
  render: ArticleList,
};

export const articleListItem = {
  render: ArticleListItem,
  selfClosing: true,
  attributes: {
    title: {
      type: String,
    },
    href: {
      type: String,
    },
  },
};

export const codeSnippet = {
  render: CodeSnippet,
  selfClosing: true,
  attributes: {
    file: {type: String, required: true},
    lang: {type: String, required: true},
    lines: {type: String},
    startafter: {type: String},
    endbefore: {type: String},
    dedent: {type: Number},
    trim: {type: Boolean, default: true},
  },
};
