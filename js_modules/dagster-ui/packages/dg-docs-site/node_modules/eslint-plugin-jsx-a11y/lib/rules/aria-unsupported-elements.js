"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
var _ariaQuery = require("aria-query");
var _jsxAstUtils = require("jsx-ast-utils");
var _schemas = require("../util/schemas");
var _getElementType = _interopRequireDefault(require("../util/getElementType"));
function _interopRequireDefault(e) { return e && e.__esModule ? e : { "default": e }; }
function _toConsumableArray(r) { return _arrayWithoutHoles(r) || _iterableToArray(r) || _unsupportedIterableToArray(r) || _nonIterableSpread(); }
function _nonIterableSpread() { throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(r, a) { if (r) { if ("string" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }
function _iterableToArray(r) { if ("undefined" != typeof Symbol && null != r[Symbol.iterator] || null != r["@@iterator"]) return Array.from(r); }
function _arrayWithoutHoles(r) { if (Array.isArray(r)) return _arrayLikeToArray(r); }
function _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; } /**
 * @fileoverview Enforce that elements that do not support ARIA roles,
 *  states and properties do not have those attributes.
 * @author Ethan Cohen
 */ // ----------------------------------------------------------------------------
// Rule Definition
// ----------------------------------------------------------------------------
var errorMessage = function errorMessage(invalidProp) {
  return "This element does not support ARIA roles, states and properties. Try removing the prop '".concat(invalidProp, "'.");
};
var schema = (0, _schemas.generateObjSchema)();
var _default = exports["default"] = {
  meta: {
    docs: {
      url: 'https://github.com/jsx-eslint/eslint-plugin-jsx-a11y/tree/HEAD/docs/rules/aria-unsupported-elements.md',
      description: 'Enforce that elements that do not support ARIA roles, states, and properties do not have those attributes.'
    },
    schema: [schema]
  },
  create: function create(context) {
    var elementType = (0, _getElementType["default"])(context);
    return {
      JSXOpeningElement: function JSXOpeningElement(node) {
        var nodeType = elementType(node);
        var nodeAttrs = _ariaQuery.dom.get(nodeType) || {};
        var _nodeAttrs$reserved = nodeAttrs.reserved,
          isReservedNodeType = _nodeAttrs$reserved === void 0 ? false : _nodeAttrs$reserved;

        // If it's not reserved, then it can have aria-* roles, states, and properties
        if (isReservedNodeType === false) {
          return;
        }
        var invalidAttributes = new Set([].concat(_toConsumableArray(_ariaQuery.aria.keys()), ['role']));
        node.attributes.forEach(function (prop) {
          if (prop.type === 'JSXSpreadAttribute') {
            return;
          }
          var name = (0, _jsxAstUtils.propName)(prop).toLowerCase();
          if (invalidAttributes.has(name)) {
            context.report({
              node,
              message: errorMessage(name)
            });
          }
        });
      }
    };
  }
};
module.exports = exports.default;