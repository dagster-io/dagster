'use strict';var _path = require('path');var _path2 = _interopRequireDefault(_path);

var _resolve = require('eslint-module-utils/resolve');var _resolve2 = _interopRequireDefault(_resolve);
var _importType = require('../core/importType');
var _moduleVisitor = require('eslint-module-utils/moduleVisitor');var _moduleVisitor2 = _interopRequireDefault(_moduleVisitor);
var _docsUrl = require('../docsUrl');var _docsUrl2 = _interopRequireDefault(_docsUrl);function _interopRequireDefault(obj) {return obj && obj.__esModule ? obj : { 'default': obj };}

var enumValues = { 'enum': ['always', 'ignorePackages', 'never'] };
var patternProperties = {
  type: 'object',
  patternProperties: { '.*': enumValues } };

var properties = {
  type: 'object',
  properties: {
    pattern: patternProperties,
    checkTypeImports: { type: 'boolean' },
    ignorePackages: { type: 'boolean' } } };



function buildProperties(context) {

  var result = {
    defaultConfig: 'never',
    pattern: {},
    ignorePackages: false };


  context.options.forEach(function (obj) {

    // If this is a string, set defaultConfig to its value
    if (typeof obj === 'string') {
      result.defaultConfig = obj;
      return;
    }

    // If this is not the new structure, transfer all props to result.pattern
    if (obj.pattern === undefined && obj.ignorePackages === undefined && obj.checkTypeImports === undefined) {
      Object.assign(result.pattern, obj);
      return;
    }

    // If pattern is provided, transfer all props
    if (obj.pattern !== undefined) {
      Object.assign(result.pattern, obj.pattern);
    }

    // If ignorePackages is provided, transfer it to result
    if (obj.ignorePackages !== undefined) {
      result.ignorePackages = obj.ignorePackages;
    }

    if (obj.checkTypeImports !== undefined) {
      result.checkTypeImports = obj.checkTypeImports;
    }
  });

  if (result.defaultConfig === 'ignorePackages') {
    result.defaultConfig = 'always';
    result.ignorePackages = true;
  }

  return result;
}

module.exports = {
  meta: {
    type: 'suggestion',
    docs: {
      category: 'Style guide',
      description: 'Ensure consistent use of file extension within the import path.',
      url: (0, _docsUrl2['default'])('extensions') },


    schema: {
      anyOf: [
      {
        type: 'array',
        items: [enumValues],
        additionalItems: false },

      {
        type: 'array',
        items: [
        enumValues,
        properties],

        additionalItems: false },

      {
        type: 'array',
        items: [properties],
        additionalItems: false },

      {
        type: 'array',
        items: [patternProperties],
        additionalItems: false },

      {
        type: 'array',
        items: [
        enumValues,
        patternProperties],

        additionalItems: false }] } },





  create: function () {function create(context) {

      var props = buildProperties(context);

      function getModifier(extension) {
        return props.pattern[extension] || props.defaultConfig;
      }

      function isUseOfExtensionRequired(extension, isPackage) {
        return getModifier(extension) === 'always' && (!props.ignorePackages || !isPackage);
      }

      function isUseOfExtensionForbidden(extension) {
        return getModifier(extension) === 'never';
      }

      function isResolvableWithoutExtension(file) {
        var extension = _path2['default'].extname(file);
        var fileWithoutExtension = file.slice(0, -extension.length);
        var resolvedFileWithoutExtension = (0, _resolve2['default'])(fileWithoutExtension, context);

        return resolvedFileWithoutExtension === (0, _resolve2['default'])(file, context);
      }

      function isExternalRootModule(file) {
        if (file === '.' || file === '..') {return false;}
        var slashCount = file.split('/').length - 1;

        if (slashCount === 0) {return true;}
        if ((0, _importType.isScoped)(file) && slashCount <= 1) {return true;}
        return false;
      }

      function checkFileExtension(source, node) {
        // bail if the declaration doesn't have a source, e.g. "export { foo };", or if it's only partially typed like in an editor
        if (!source || !source.value) {return;}

        var importPathWithQueryString = source.value;

        // don't enforce anything on builtins
        if ((0, _importType.isBuiltIn)(importPathWithQueryString, context.settings)) {return;}

        var importPath = importPathWithQueryString.replace(/\?(.*)$/, '');

        // don't enforce in root external packages as they may have names with `.js`.
        // Like `import Decimal from decimal.js`)
        if (isExternalRootModule(importPath)) {return;}

        var resolvedPath = (0, _resolve2['default'])(importPath, context);

        // get extension from resolved path, if possible.
        // for unresolved, use source value.
        var extension = _path2['default'].extname(resolvedPath || importPath).substring(1);

        // determine if this is a module
        var isPackage = (0, _importType.isExternalModule)(
        importPath,
        (0, _resolve2['default'])(importPath, context),
        context) ||
        (0, _importType.isScoped)(importPath);

        if (!extension || !importPath.endsWith('.' + String(extension))) {
          // ignore type-only imports and exports
          if (!props.checkTypeImports && (node.importKind === 'type' || node.exportKind === 'type')) {return;}
          var extensionRequired = isUseOfExtensionRequired(extension, isPackage);
          var extensionForbidden = isUseOfExtensionForbidden(extension);
          if (extensionRequired && !extensionForbidden) {
            context.report({
              node: source,
              message: 'Missing file extension ' + (
              extension ? '"' + String(extension) + '" ' : '') + 'for "' + String(importPathWithQueryString) + '"' });

          }
        } else if (extension) {
          if (isUseOfExtensionForbidden(extension) && isResolvableWithoutExtension(importPath)) {
            context.report({
              node: source,
              message: 'Unexpected use of file extension "' + String(extension) + '" for "' + String(importPathWithQueryString) + '"' });

          }
        }
      }

      return (0, _moduleVisitor2['default'])(checkFileExtension, { commonjs: true });
    }return create;}() };
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIi4uLy4uL3NyYy9ydWxlcy9leHRlbnNpb25zLmpzIl0sIm5hbWVzIjpbImVudW1WYWx1ZXMiLCJwYXR0ZXJuUHJvcGVydGllcyIsInR5cGUiLCJwcm9wZXJ0aWVzIiwicGF0dGVybiIsImNoZWNrVHlwZUltcG9ydHMiLCJpZ25vcmVQYWNrYWdlcyIsImJ1aWxkUHJvcGVydGllcyIsImNvbnRleHQiLCJyZXN1bHQiLCJkZWZhdWx0Q29uZmlnIiwib3B0aW9ucyIsImZvckVhY2giLCJvYmoiLCJ1bmRlZmluZWQiLCJPYmplY3QiLCJhc3NpZ24iLCJtb2R1bGUiLCJleHBvcnRzIiwibWV0YSIsImRvY3MiLCJjYXRlZ29yeSIsImRlc2NyaXB0aW9uIiwidXJsIiwic2NoZW1hIiwiYW55T2YiLCJpdGVtcyIsImFkZGl0aW9uYWxJdGVtcyIsImNyZWF0ZSIsInByb3BzIiwiZ2V0TW9kaWZpZXIiLCJleHRlbnNpb24iLCJpc1VzZU9mRXh0ZW5zaW9uUmVxdWlyZWQiLCJpc1BhY2thZ2UiLCJpc1VzZU9mRXh0ZW5zaW9uRm9yYmlkZGVuIiwiaXNSZXNvbHZhYmxlV2l0aG91dEV4dGVuc2lvbiIsImZpbGUiLCJwYXRoIiwiZXh0bmFtZSIsImZpbGVXaXRob3V0RXh0ZW5zaW9uIiwic2xpY2UiLCJsZW5ndGgiLCJyZXNvbHZlZEZpbGVXaXRob3V0RXh0ZW5zaW9uIiwiaXNFeHRlcm5hbFJvb3RNb2R1bGUiLCJzbGFzaENvdW50Iiwic3BsaXQiLCJjaGVja0ZpbGVFeHRlbnNpb24iLCJzb3VyY2UiLCJub2RlIiwidmFsdWUiLCJpbXBvcnRQYXRoV2l0aFF1ZXJ5U3RyaW5nIiwic2V0dGluZ3MiLCJpbXBvcnRQYXRoIiwicmVwbGFjZSIsInJlc29sdmVkUGF0aCIsInN1YnN0cmluZyIsImVuZHNXaXRoIiwiaW1wb3J0S2luZCIsImV4cG9ydEtpbmQiLCJleHRlbnNpb25SZXF1aXJlZCIsImV4dGVuc2lvbkZvcmJpZGRlbiIsInJlcG9ydCIsIm1lc3NhZ2UiLCJjb21tb25q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QUExQixDQUEzQjtBQUNBLGNBQUk0QixxQkFBcUIsQ0FBQ0Msa0JBQTFCLEVBQThDO0FBQzVDcEQsb0JBQVFxRCxNQUFSLENBQWU7QUFDYmIsb0JBQU1ELE1BRE87QUFFYmU7QUFDNEIvQix1Q0FBZ0JBLFNBQWhCLFdBQWdDLEVBRDVELHFCQUNzRW1CLHlCQUR0RSxPQUZhLEVBQWY7O0FBS0Q7QUFDRixTQVpELE1BWU8sSUFBSW5CLFNBQUosRUFBZTtBQUNwQixjQUFJRywwQkFBMEJILFNBQTFCLEtBQXdDSSw2QkFBNkJpQixVQUE3QixDQUE1QyxFQUFzRjtBQUNwRjVDLG9CQUFRcUQsTUFBUixDQUFlO0FBQ2JiLG9CQUFNRCxNQURPO0FBRWJlLHFFQUE4Qy9CLFNBQTlDLHVCQUFpRW1CLHlCQUFqRSxPQUZhLEVBQWY7O0FBSUQ7QUFDRjtBQUNGOztBQUVELGFBQU8sZ0NBQWNKLGtCQUFkLEVBQWtDLEVBQUVpQixVQUFVLElBQVosRUFBbEMsQ0FBUDtBQUNELEtBbEljLG1CQUFqQiIsImZpbGUiOiJleHRlbnNpb25zLmpzIiwic291cmNlc0NvbnRlbnQiOlsiaW1wb3J0IHBhdGggZnJvbSAncGF0aCc7XG5cbmltcG9ydCByZXNvbHZlIGZyb20gJ2VzbGludC1tb2R1bGUtdXRpbHMvcmVzb2x2ZSc7XG5pbXBvcnQgeyBpc0J1aWx0SW4sIGlzRXh0ZXJuYWxNb2R1bGUsIGlzU2NvcGVkIH0gZnJvbSAnLi4vY29yZS9pbXBvcnRUeXBlJztcbmltcG9ydCBtb2R1bGVWaXNpdG9yIGZyb20gJ2VzbGludC1tb2R1bGUtdXRpbHMvbW9kdWxlVmlzaXRvcic7XG5pbXBvcnQgZG9jc1VybCBmcm9tICcuLi9kb2NzVXJsJztcblxuY29uc3QgZW51bVZhbHVlcyA9IHsgZW51bTogWydhbHdheXMnLCAnaWdub3JlUGFja2FnZXMnLCAnbmV2ZXInXSB9O1xuY29uc3QgcGF0dGVyblByb3BlcnRpZXMgPSB7XG4gIHR5cGU6ICdvYmplY3QnLFxuICBwYXR0ZXJuUHJvcGVydGllczogeyAnLionOiBlbnVtVmFsdWVzIH0sXG59O1xuY29uc3QgcHJvcGVydGllcyA9IHtcbiAgdHlwZTogJ29iamVjdCcsXG4gIHByb3BlcnRpZXM6IHtcbiAgICBwYXR0ZXJuOiBwYXR0ZXJuUHJvcGVydGllcyxcbiAgICBjaGVja1R5cGVJbXBvcnRzOiB7IHR5cGU6ICdib29sZWFuJyB9LFxuICAgIGlnbm9yZVBhY2thZ2VzOiB7IHR5cGU6ICdib29sZWFuJyB9LFxuICB9LFxufTtcblxuZnVuY3Rpb24gYnVpbGRQcm9wZXJ0aWVzKGNvbnRleHQpIHtcblxuICBjb25zdCByZXN1bHQgPSB7XG4gICAgZGVmYXVsdENvbmZpZzogJ25ldmVyJyxcbiAgICBwYXR0ZXJuOiB7fSxcbiAgICBpZ25vcmVQYWNrYWdlczogZmFsc2UsXG4gIH07XG5cbiAgY29udGV4dC5vcHRpb25zLmZvckVhY2goKG9iaikgPT4ge1xuXG4gICAgLy8gSWYgdGhpcyBpcyBhIHN0cmluZywgc2V0IGRlZmF1bHRDb25maWcgdG8gaXRzIHZhbHVlXG4gICAgaWYgKHR5cGVvZiBvYmogPT09ICdzdHJpbmcnKSB7XG4gICAgICByZXN1bHQuZGVmYXVsdENvbmZpZyA9IG9iajtcbiAgICAgIHJldHVybjtcbiAgICB9XG5cbiAgICAvLyBJZiB0aGlzIGlzIG5vdCB0aGUgbmV3IHN0cnVjdHVyZSwgdHJhbnNmZXIgYWxsIHByb3BzIHRvIHJlc3VsdC5wYXR0ZXJuXG4gICAgaWYgKG9iai5wYXR0ZXJuID09PSB1bmRlZmluZWQgJiYgb2JqLmlnbm9yZVBhY2thZ2VzID09PSB1bmRlZmluZWQgJiYgb2JqLmNoZWNrVHlwZUltcG9ydHMgPT09IHVuZGVmaW5lZCkge1xuICAgICAgT2JqZWN0LmFzc2lnbihyZXN1bHQucGF0dGVybiwgb2JqKTtcbiAgICAgIHJldHVybjtcbiAgICB9XG5cbiAgICAvLyBJZiBwYXR0ZXJuIGlzIHByb3ZpZGVkLCB0cmFuc2ZlciBhbGwgcHJvcHNcbiAgICBpZiAob2JqLnBhdHRlcm4gIT09IHVuZGVmaW5lZCkge1xuICAgICAgT2JqZWN0LmFzc2lnbihyZXN1bHQucGF0dGVybiwgb2JqLnBhdHRlcm4pO1xuICAgIH1cblxuICAgIC8vIElmIGlnbm9yZVBhY2thZ2VzIGlzIHByb3ZpZGVkLCB0cmFuc2ZlciBpdCB0byByZXN1bHRcbiAgICBpZiAob2JqLmlnbm9yZVBhY2thZ2VzICE9PSB1bmRlZmluZWQpIHtcbiAgICAgIHJlc3VsdC5pZ25vcmVQYWNrYWdlcyA9IG9iai5pZ25vcmVQYWNrYWdlcztcbiAgICB9XG5cbiAgICBpZiAob2JqLmNoZWNrVHlwZUltcG9ydHMgIT09IHVuZGVmaW5lZCkge1xuICAgICAgcmVzdWx0LmNoZWNrVHlwZUltcG9ydHMgPSBvYmouY2hlY2tUeXBlSW1wb3J0cztcbiAgICB9XG4gIH0pO1xuXG4gIGlmIChyZXN1bHQuZGVmYXVsdENvbmZpZyA9PT0gJ2lnbm9yZVBhY2thZ2VzJykge1xuICAgIHJlc3VsdC5kZWZhdWx0Q29uZmlnID0gJ2Fsd2F5cyc7XG4gICAgcmVzdWx0Lmlnbm9yZVBhY2thZ2VzID0gdHJ1ZTtcbiAgfVxuXG4gIHJldHVybiByZXN1bHQ7XG59XG5cbm1vZHVsZS5leHBvcnRzID0ge1xuICBtZXRhOiB7XG4gICAgdHlwZTogJ3N1Z2dlc3Rpb24nLFxuICAgIGRvY3M6IHtcbiAgICAgIGNhdGVnb3J5OiAnU3R5bGUgZ3VpZGUnLFxuICAgICAgZGVzY3JpcHRpb246ICdFbnN1cmUgY29uc2lzdGVudCB1c2Ugb2YgZmlsZSBleHRlbnNpb24gd2l0aGluIHRoZSBpbXBvcnQgcGF0aC4nLFxuICAgICAgdXJsOiBkb2NzVXJsKCdleHRlbnNpb25zJyksXG4gICAgfSxcblxuICAgIHNjaGVtYToge1xuICAgICAgYW55T2Y6IFtcbiAgICAgICAge1xuICAgICAgICAgIHR5cGU6ICdhcnJheScsXG4gICAgICAgICAgaXRlbXM6IFtlbnVtVmFsdWVzXSxcbiAgICAgICAgICBhZGRpdGlvbmFsSXRlbXM6IGZhbHNlLFxuICAgICAgICB9LFxuICAgICAgICB7XG4gICAgICAgICAgdHlwZTogJ2FycmF5JyxcbiAgICAgICAgICBpdGVtczogW1xuICAgICAgICAgICAgZW51bVZhbHVlcyxcbiAgICAgICAgICAgIHByb3BlcnRpZXMsXG4gICAgICAgICAgXSxcbiAgICAgICAgICBhZGRpdGlvbmFsSXRlbXM6IGZhbHNlLFxuICAgICAgICB9LFxuICAgICAgICB7XG4gICAgICAgICAgdHlwZTogJ2FycmF5JyxcbiAgICAgICAgICBpdGVtczogW3Byb3BlcnRpZXNdLFxuICAgICAgICAgIGFkZGl0aW9uYWxJdGVtczogZmFsc2UsXG4gICAgICAgIH0sXG4gICAgICAgIHtcbiAgICAgICAgICB0eXBlOiAnYXJyYXknLFxuICAgICAgICAgIGl0ZW1zOiBbcGF0dGVyblByb3BlcnRpZXNdLFxuICAgICAgICAgIGFkZGl0aW9uYWxJdGVtczogZmFsc2UsXG4gICAgICAgIH0sXG4gICAgICAgIHtcbiAgICAgICAgICB0eXBlOiAnYXJyYXknLFxuICAgICAgICAgIGl0ZW1zOiBbXG4gICAgICAgICAgICBlbnVtVmFsdWVzLFxuICAgICAgICAgICAgcGF0dGVyblByb3BlcnRpZXMsXG4gICAgICAgICAgXSxcbiAgICAgICAgICBhZGRpdGlvbmFsSXRlbXM6IGZhbHNlLFxuICAgICAgICB9LFxuICAgICAgXSxcbiAgICB9LFxuICB9LFxuXG4gIGNyZWF0ZShjb250ZXh0KSB7XG5cbiAgICBjb25zdCBwcm9wcyA9IGJ1aWxkUHJvcGVydGllcyhjb250ZXh0KTtcblxuICAgIGZ1bmN0aW9uIGdldE1vZGlmaWVyKGV4dGVuc2lvbikge1xuICAgICAgcmV0dXJuIHByb3BzLnBhdHRlcm5bZXh0ZW5zaW9uXSB8fCBwcm9wcy5kZWZhdWx0Q29uZmlnO1xuICAgIH1cblxuICAgIGZ1bmN0aW9uIGlzVXNlT2ZFeHRlbnNpb25SZXF1aXJlZChleHRlbnNpb24sIGlzUGFja2FnZSkge1xuICAgICAgcmV0dXJuIGdldE1vZGlmaWVyKGV4dGVuc2lvbikgPT09ICdhbHdheXMnICYmICghcHJvcHMuaWdub3JlUGFja2FnZXMgfHwgIWlzUGFja2FnZSk7XG4gICAgfVxuXG4gICAgZnVuY3Rpb24gaXNVc2VPZkV4dGVuc2lvbkZvcmJpZGRlbihleHRlbnNpb24pIHtcbiAgICAgIHJldHVybiBnZXRNb2RpZmllcihleHRlbnNpb24pID09PSAnbmV2ZXInO1xuICAgIH1cblxuICAgIGZ1bmN0aW9uIGlzUmVzb2x2YWJsZVdpdGhvdXRFeHRlbnNpb24oZmlsZSkge1xuICAgICAgY29uc3QgZXh0ZW5zaW9uID0gcGF0aC5leHRuYW1lKGZpbGUpO1xuICAgICAgY29uc3QgZmlsZVdpdGhvdXRFeHRlbnNpb24gPSBmaWxlLnNsaWNlKDAsIC1leHRlbnNpb24ubGVuZ3RoKTtcbiAgICAgIGNvbnN0IHJlc29sdmVkRmlsZVdpdGhvdXRFeHRlbnNpb24gPSByZXNvbHZlKGZpbGVXaXRob3V0RXh0ZW5zaW9uLCBjb250ZXh0KTtcblxuICAgICAgcmV0dXJuIHJlc29sdmVkRmlsZVdpdGhvdXRFeHRlbnNpb24gPT09IHJlc29sdmUoZmlsZSwgY29udGV4dCk7XG4gICAgfVxuXG4gICAgZnVuY3Rpb24gaXNFeHRlcm5hbFJvb3RNb2R1bGUoZmlsZSkge1xuICAgICAgaWYgKGZpbGUgPT09ICcuJyB8fCBmaWxlID09PSAnLi4nKSB7IHJldHVybiBmYWxzZTsgfVxuICAgICAgY29uc3Qgc2xhc2hDb3VudCA9IGZpbGUuc3BsaXQoJy8nKS5sZW5ndGggLSAxO1xuXG4gICAgICBpZiAoc2xhc2hDb3VudCA9PT0gMCkgIHsgcmV0dXJuIHRydWU7IH1cbiAgICAgIGlmIChpc1Njb3BlZChmaWxlKSAmJiBzbGFzaENvdW50IDw9IDEpIHsgcmV0dXJuIHRydWU7IH1cbiAgICAgIHJldHVybiBmYWxzZTtcbiAgICB9XG5cbiAgICBmdW5jdGlvbiBjaGVja0ZpbGVFeHRlbnNpb24oc291cmNlLCBub2RlKSB7XG4gICAgICAvLyBiYWlsIGlmIHRoZSBkZWNsYXJhdGlvbiBkb2Vzbid0IGhhdmUgYSBzb3VyY2UsIGUuZy4gXCJleHBvcnQgeyBmb28gfTtcIiwgb3IgaWYgaXQncyBvbmx5IHBhcnRpYWxseSB0eXBlZCBsaWtlIGluIGFuIGVkaXRvclxuICAgICAgaWYgKCFzb3VyY2UgfHwgIXNvdXJjZS52YWx1ZSkgeyByZXR1cm47IH1cblxuICAgICAgY29uc3QgaW1wb3J0UGF0aFdpdGhRdWVyeVN0cmluZyA9IHNvdXJjZS52YWx1ZTtcblxuICAgICAgLy8gZG9uJ3QgZW5mb3JjZSBhbnl0aGluZyBvbiBidWlsdGluc1xuICAgICAgaWYgKGlzQnVpbHRJbihpbXBvcnRQYXRoV2l0aFF1ZXJ5U3RyaW5nLCBjb250ZXh0LnNldHRpbmdzKSkgeyByZXR1cm47IH1cblxuICAgICAgY29uc3QgaW1wb3J0UGF0aCA9IGltcG9ydFBhdGhXaXRoUXVlcnlTdHJpbmcucmVwbGFjZSgvXFw/KC4qKSQvLCAnJyk7XG5cbiAgICAgIC8vIGRvbid0IGVuZm9yY2UgaW4gcm9vdCBleHRlcm5hbCBwYWNrYWdlcyBhcyB0aGV5IG1heSBoYXZlIG5hbWVzIHdpdGggYC5qc2AuXG4gICAgICAvLyBMaWtlIGBpbXBvcnQgRGVjaW1hbCBmcm9tIGRlY2ltYWwuanNgKVxuICAgICAgaWYgKGlzRXh0ZXJuYWxSb290TW9kdWxlKGltcG9ydFBhdGgpKSB7IHJldHVybjsgfVxuXG4gICAgICBjb25zdCByZXNvbHZlZFBhdGggPSByZXNvbHZlKGltcG9ydFBhdGgsIGNvbnRleHQpO1xuXG4gICAgICAvLyBnZXQgZXh0ZW5zaW9uIGZyb20gcmVzb2x2ZWQgcGF0aCwgaWYgcG9zc2libGUuXG4gICAgICAvLyBmb3IgdW5yZXNvbHZlZCwgdXNlIHNvdXJjZSB2YWx1ZS5cbiAgICAgIGNvbnN0IGV4dGVuc2lvbiA9IHBhdGguZXh0bmFtZShyZXNvbHZlZFBhdGggfHwgaW1wb3J0UGF0aCkuc3Vic3RyaW5nKDEpO1xuXG4gICAgICAvLyBkZXRlcm1pbmUgaWYgdGhpcyBpcyBhIG1vZHVsZVxuICAgICAgY29uc3QgaXNQYWNrYWdlID0gaXNFeHRlcm5hbE1vZHVsZShcbiAgICAgICAgaW1wb3J0UGF0aCxcbiAgICAgICAgcmVzb2x2ZShpbXBvcnRQYXRoLCBjb250ZXh0KSxcbiAgICAgICAgY29udGV4dCxcbiAgICAgICkgfHwgaXNTY29wZWQoaW1wb3J0UGF0aCk7XG5cbiAgICAgIGlmICghZXh0ZW5zaW9uIHx8ICFpbXBvcnRQYXRoLmVuZHNXaXRoKGAuJHtleHRlbnNpb259YCkpIHtcbiAgICAgICAgLy8gaWdub3JlIHR5cGUtb25seSBpbXBvcnRzIGFuZCBleHBvcnRzXG4gICAgICAgIGlmICghcHJvcHMuY2hlY2tUeXBlSW1wb3J0cyAmJiAobm9kZS5pbXBvcnRLaW5kID09PSAndHlwZScgfHwgbm9kZS5leHBvcnRLaW5kID09PSAndHlwZScpKSB7IHJldHVybjsgfVxuICAgICAgICBjb25zdCBleHRlbnNpb25SZXF1aXJlZCA9IGlzVXNlT2ZFeHRlbnNpb25SZXF1aXJlZChleHRlbnNpb24sIGlzUGFja2FnZSk7XG4gICAgICAgIGNvbnN0IGV4dGVuc2lvbkZvcmJpZGRlbiA9IGlzVXNlT2ZFeHRlbnNpb25Gb3JiaWRkZW4oZXh0ZW5zaW9uKTtcbiAgICAgICAgaWYgKGV4dGVuc2lvblJlcXVpcmVkICYmICFleHRlbnNpb25Gb3JiaWRkZW4pIHtcbiAgICAgICAgICBjb250ZXh0LnJlcG9ydCh7XG4gICAgICAgICAgICBub2RlOiBzb3VyY2UsXG4gICAgICAgICAgICBtZXNzYWdlOlxuICAgICAgICAgICAgICBgTWlzc2luZyBmaWxlIGV4dGVuc2lvbiAke2V4dGVuc2lvbiA/IGBcIiR7ZXh0ZW5zaW9ufVwiIGAgOiAnJ31mb3IgXCIke2ltcG9ydFBhdGhXaXRoUXVlcnlTdHJpbmd9XCJgLFxuICAgICAgICAgIH0pO1xuICAgICAgICB9XG4gICAgICB9IGVsc2UgaWYgKGV4dGVuc2lvbikge1xuICAgICAgICBpZiAoaXNVc2VPZkV4dGVuc2lvbkZvcmJpZGRlbihleHRlbnNpb24pICYmIGlzUmVzb2x2YWJsZVdpdGhvdXRFeHRlbnNpb24oaW1wb3J0UGF0aCkpIHtcbiAgICAgICAgICBjb250ZXh0LnJlcG9ydCh7XG4gICAgICAgICAgICBub2RlOiBzb3VyY2UsXG4gICAgICAgICAgICBtZXNzYWdlOiBgVW5leHBlY3RlZCB1c2Ugb2YgZmlsZSBleHRlbnNpb24gXCIke2V4dGVuc2lvbn1cIiBmb3IgXCIke2ltcG9ydFBhdGhXaXRoUXVlcnlTdHJpbmd9XCJgLFxuICAgICAgICAgIH0pO1xuICAgICAgICB9XG4gICAgICB9XG4gICAgfVxuXG4gICAgcmV0dXJuIG1vZHVsZVZpc2l0b3IoY2hlY2tGaWxlRXh0ZW5zaW9uLCB7IGNvbW1vbmpzOiB0cnVlIH0pO1xuICB9LFxufTtcbiJdfQ==