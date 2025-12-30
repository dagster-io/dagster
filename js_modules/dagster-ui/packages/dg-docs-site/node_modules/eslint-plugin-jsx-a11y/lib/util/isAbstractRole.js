"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
var _ariaQuery = require("aria-query");
var _jsxAstUtils = require("jsx-ast-utils");
var _Iterator = _interopRequireDefault(require("es-iterator-helpers/Iterator.from"));
var _IteratorPrototype = _interopRequireDefault(require("es-iterator-helpers/Iterator.prototype.filter"));
function _interopRequireDefault(e) { return e && e.__esModule ? e : { "default": e }; }
var abstractRoles = new Set((0, _IteratorPrototype["default"])((0, _Iterator["default"])(_ariaQuery.roles.keys()), function (role) {
  return _ariaQuery.roles.get(role)["abstract"];
}));
var DOMElements = new Set(_ariaQuery.dom.keys());
var isAbstractRole = function isAbstractRole(tagName, attributes) {
  // Do not test higher level JSX components, as we do not know what
  // low-level DOM element this maps to.
  if (!DOMElements.has(tagName)) {
    return false;
  }
  var role = (0, _jsxAstUtils.getLiteralPropValue)((0, _jsxAstUtils.getProp)(attributes, 'role'));
  return abstractRoles.has(role);
};
var _default = exports["default"] = isAbstractRole;
module.exports = exports.default;