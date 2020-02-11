const R = require("ramda");

const getPath = pageName => {
  return pageName.endsWith("/index")
    ? pageName.replace("/index", "")
    : pageName;
};

const checkNodeBeforeCreatePage = node => {
  const pageName = node.current_page_name;
  if (!pageName) return;
  if (["genindex", "index", "py-modindex"].some(R.equals(pageName))) return;
  return Boolean(node.title);
};

exports.getSlug = node => {
  if (!checkNodeBeforeCreatePage(node)) return null;
  return getPath(node.current_page_name).replace("sections/", "");
};
