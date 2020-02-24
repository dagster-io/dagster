const unified = require("unified");
const parse = require("rehype-parse");
const sanitize = require("rehype-sanitize");
const has = require("hast-util-has-property");
const stringify = require("rehype-stringify");
const rehype2remark = require("rehype-remark");
const markdown = require("remark-stringify");
const map = require("unist-util-map");
const strip = require("strip-markdown");
const parse5 = require("parse5");
const minify = require("rehype-preset-minify");
const { produce } = require("immer");
const Flatted = require("flatted");
const { getCurrentVersion } = require("./utils/get-version");

const rewriteLinks = (node, version) => {
  const modulesRegex = /^(..\/)+_modules\//g;
  var url = node.properties.href
    .replace(modulesRegex, `/${version}/_modules/`)
    .replace("/sections/", "/");
  if (url.startsWith("sections/")) {
    url = url.slice(9, Infinity);
  }
  node.properties.href = url;
};

const addExternalAttributes = node => {
  const { className } = node.properties;
  if (className && className.includes("external")) {
    node.properties.target = "_blank";
    node.properties.rel = "noopener noreferrer";
  }
};

const addPermalinkClass = node => {
  node.properties.className = "permalink";
};

const rewriteImages = node => {
  const url = node.properties.src;
  if (/_images/.test(url)) {
    const newUrl = url.match(/(.+)(_images\/)(.+)/)[3];
    node.properties.src = newUrl;
    node.properties.alt = newUrl;
  }
};

const isCodeSection = node => {
  return has(node, "id") && /id[0-9]/.test(node.properties.id);
};

const rewriteTree = version =>
  produce(node => {
    if (node.tagName === "a") {
      rewriteLinks(node, version);
      addExternalAttributes(node);
    }
    if (node.tagName === "img") {
      rewriteImages(node);
    }
    if (node.value === "¶") {
      node.value = "#";
    }
    if (node.tagName === "a") {
      addPermalinkClass(node);
    }
    if (isCodeSection(node)) {
      node.properties.className = "code-section";
    }

    return node;
  });

const parseHtml = (body, version) => {
  const processor = unified()
    .use(parse)
    .use(sanitize);

  const tree = processor.parse(body);
  const newTree = map(tree, rewriteTree(version));

  return unified()
    .use(stringify)
    .use(minify)
    .stringify(newTree)
    .replace(/^<html><head><\/head><body>/, "")
    .replace(/\n<\/body><\/html>$/, "");
};

const parseMarkdown = (body, version) => {
  const html = parseHtml(body, version);
  return unified()
    .use(parse)
    .use(rehype2remark)
    .use(markdown)
    .use(strip, { keep: ["code"] })
    .processSync(html)
    .toString();
};

exports.parseHtml = parseHtml;
exports.parseMarkdown = parseMarkdown;

exports.toParseFive = body => {
  const html = parseHtml(body, getCurrentVersion());
  const parsed = parse5.parse(html, { sourceCodeLocationInfo: false });

  return Flatted.stringify(parsed);
};

exports.parseToc = body => {
  const html = parseHtml(body, getCurrentVersion());
  const parsed = parse5.parse(html, { sourceCodeLocationInfo: false });
  return Flatted.stringify(parsed);
};
