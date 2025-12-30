"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
var _ariaQuery = require("aria-query");
var _jsxAstUtils = require("jsx-ast-utils");
var _schemas = require("../util/schemas");
var _getSuggestion = _interopRequireDefault(require("../util/getSuggestion"));
function _interopRequireDefault(e) { return e && e.__esModule ? e : { "default": e }; }
function _toConsumableArray(r) { return _arrayWithoutHoles(r) || _iterableToArray(r) || _unsupportedIterableToArray(r) || _nonIterableSpread(); }
function _nonIterableSpread() { throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(r, a) { if (r) { if ("string" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }
function _iterableToArray(r) { if ("undefined" != typeof Symbol && null != r[Symbol.iterator] || null != r["@@iterator"]) return Array.from(r); }
function _arrayWithoutHoles(r) { if (Array.isArray(r)) return _arrayLikeToArray(r); }
function _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; } /**
 * @fileoverview Enforce all aria-* properties are valid.
 * @author Ethan Cohen
 */ // ----------------------------------------------------------------------------
// Rule Definition
// ----------------------------------------------------------------------------
var ariaAttributes = _toConsumableArray(_ariaQuery.aria.keys());
var errorMessage = function errorMessage(name) {
  var suggestions = (0, _getSuggestion["default"])(name, ariaAttributes);
  var message = "".concat(name, ": This attribute is an invalid ARIA attribute.");
  if (suggestions.length > 0) {
    return "".concat(message, " Did you mean to use ").concat(suggestions, "?");
  }
  return message;
};
var schema = (0, _schemas.generateObjSchema)();
var _default = exports["default"] = {
  meta: {
    docs: {
      url: 'https://github.com/jsx-eslint/eslint-plugin-jsx-a11y/tree/HEAD/docs/rules/aria-props.md',
      description: 'Enforce all `aria-*` props are valid.'
    },
    schema: [schema]
  },
  create: function create(context) {
    return {
      JSXAttribute: function JSXAttribute(attribute) {
        var name = (0, _jsxAstUtils.propName)(attribute);

        // `aria` needs to be prefix of property.
        if (name.indexOf('aria-') !== 0) {
          return;
        }
        var isValid = _ariaQuery.aria.has(name);
        if (isValid === false) {
          context.report({
            node: attribute,
            message: errorMessage(name)
          });
        }
      }
    };
  }
};
module.exports = exports.default;