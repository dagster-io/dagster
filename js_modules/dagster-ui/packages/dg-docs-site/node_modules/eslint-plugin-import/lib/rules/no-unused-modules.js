'use strict';var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) {return typeof obj;} : function (obj) {return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj;};





var _contextCompat = require('eslint-module-utils/contextCompat');
var _ignore = require('eslint-module-utils/ignore');
var _resolve = require('eslint-module-utils/resolve');var _resolve2 = _interopRequireDefault(_resolve);
var _visit = require('eslint-module-utils/visit');var _visit2 = _interopRequireDefault(_visit);
var _path = require('path');
var _readPkgUp2 = require('eslint-module-utils/readPkgUp');var _readPkgUp3 = _interopRequireDefault(_readPkgUp2);
var _object = require('object.values');var _object2 = _interopRequireDefault(_object);
var _arrayIncludes = require('array-includes');var _arrayIncludes2 = _interopRequireDefault(_arrayIncludes);
var _arrayPrototype = require('array.prototype.flatmap');var _arrayPrototype2 = _interopRequireDefault(_arrayPrototype);

var _fsWalk = require('../core/fsWalk');
var _builder = require('../exportMap/builder');var _builder2 = _interopRequireDefault(_builder);
var _patternCapture = require('../exportMap/patternCapture');var _patternCapture2 = _interopRequireDefault(_patternCapture);
var _docsUrl = require('../docsUrl');var _docsUrl2 = _interopRequireDefault(_docsUrl);function _interopRequireDefault(obj) {return obj && obj.__esModule ? obj : { 'default': obj };}function _toConsumableArray(arr) {if (Array.isArray(arr)) {for (var i = 0, arr2 = Array(arr.length); i < arr.length; i++) {arr2[i] = arr[i];}return arr2;} else {return Array.from(arr);}} /**
                                                                                                                                                                                                                                                                                                                                                                                 * @fileOverview Ensures that modules contain exports and/or all
                                                                                                                                                                                                                                                                                                                                                                                 * modules are consumed within other modules.
                                                                                                                                                                                                                                                                                                                                                                                 * @author René Fermann
                                                                                                                                                                                                                                                                                                                                                                                 */ /**
                                                                                                                                                                                                                                                                                                                                                                                     * Attempt to load the internal `FileEnumerator` class, which has existed in a couple
                                                                                                                                                                                                                                                                                                                                                                                     * of different places, depending on the version of `eslint`.  Try requiring it from both
                                                                                                                                                                                                                                                                                                                                                                                     * locations.
                                                                                                                                                                                                                                                                                                                                                                                     * @returns Returns the `FileEnumerator` class if its requirable, otherwise `undefined`.
                                                                                                                                                                                                                                                                                                                                                                                     */function requireFileEnumerator() {var FileEnumerator = void 0;

  // Try getting it from the eslint private / deprecated api
  try {var _require =
    require('eslint/use-at-your-own-risk');FileEnumerator = _require.FileEnumerator;
  } catch (e) {
    // Absorb this if it's MODULE_NOT_FOUND
    if (e.code !== 'MODULE_NOT_FOUND') {
      throw e;
    }

    // If not there, then try getting it from eslint/lib/cli-engine/file-enumerator (moved there in v6)
    try {var _require2 =
      require('eslint/lib/cli-engine/file-enumerator');FileEnumerator = _require2.FileEnumerator;
    } catch (e) {
      // Absorb this if it's MODULE_NOT_FOUND
      if (e.code !== 'MODULE_NOT_FOUND') {
        throw e;
      }
    }
  }
  return FileEnumerator;
}

/**
   *
   * @param FileEnumerator the `FileEnumerator` class from `eslint`'s internal api
   * @param {string} src path to the src root
   * @param {string[]} extensions list of supported extensions
   * @returns {{ filename: string, ignored: boolean }[]} list of files to operate on
   */
function listFilesUsingFileEnumerator(FileEnumerator, src, extensions) {
  var e = new FileEnumerator({
    extensions: extensions });


  return Array.from(
  e.iterateFiles(src),
  function (_ref) {var filePath = _ref.filePath,ignored = _ref.ignored;return { filename: filePath, ignored: ignored };});

}

/**
   * Attempt to require old versions of the file enumeration capability from v6 `eslint` and earlier, and use
   * those functions to provide the list of files to operate on
   * @param {string} src path to the src root
   * @param {string[]} extensions list of supported extensions
   * @returns {string[]} list of files to operate on
   */
function listFilesWithLegacyFunctions(src, extensions) {
  try {
    // eslint/lib/util/glob-util has been moved to eslint/lib/util/glob-utils with version 5.3
    var _require3 = require('eslint/lib/util/glob-utils'),originalListFilesToProcess = _require3.listFilesToProcess;
    // Prevent passing invalid options (extensions array) to old versions of the function.
    // https://github.com/eslint/eslint/blob/v5.16.0/lib/util/glob-utils.js#L178-L280
    // https://github.com/eslint/eslint/blob/v5.2.0/lib/util/glob-util.js#L174-L269

    return originalListFilesToProcess(src, {
      extensions: extensions });

  } catch (e) {
    // Absorb this if it's MODULE_NOT_FOUND
    if (e.code !== 'MODULE_NOT_FOUND') {
      throw e;
    }

    // Last place to try (pre v5.3)
    var _require4 =

    require('eslint/lib/util/glob-util'),_originalListFilesToProcess = _require4.listFilesToProcess;
    var patterns = src.concat(
    (0, _arrayPrototype2['default'])(
    src,
    function (pattern) {return extensions.map(function (extension) {return (/\*\*|\*\./.test(pattern) ? pattern : String(pattern) + '/**/*' + String(extension));});}));



    return _originalListFilesToProcess(patterns);
  }
}

/**
   * Given a source root and list of supported extensions, use fsWalk and the
   * new `eslint` `context.session` api to build the list of files we want to operate on
   * @param {string[]} srcPaths array of source paths (for flat config this should just be a singular root (e.g. cwd))
   * @param {string[]} extensions list of supported extensions
   * @param {{ isDirectoryIgnored: (path: string) => boolean, isFileIgnored: (path: string) => boolean }} session eslint context session object
   * @returns {string[]} list of files to operate on
   */
function listFilesWithModernApi(srcPaths, extensions, session) {
  /** @type {string[]} */
  var files = [];var _loop = function _loop(

  i) {
    var src = srcPaths[i];
    // Use walkSync along with the new session api to gather the list of files
    var entries = (0, _fsWalk.walkSync)(src, {
      deepFilter: function () {function deepFilter(entry) {
          var fullEntryPath = (0, _path.resolve)(src, entry.path);

          // Include the directory if it's not marked as ignore by eslint
          return !session.isDirectoryIgnored(fullEntryPath);
        }return deepFilter;}(),
      entryFilter: function () {function entryFilter(entry) {
          var fullEntryPath = (0, _path.resolve)(src, entry.path);

          // Include the file if it's not marked as ignore by eslint and its extension is included in our list
          return (
            !session.isFileIgnored(fullEntryPath) &&
            extensions.find(function (extension) {return entry.path.endsWith(extension);}));

        }return entryFilter;}() });


    // Filter out directories and map entries to their paths
    files.push.apply(files, _toConsumableArray(
    entries.
    filter(function (entry) {return !entry.dirent.isDirectory();}).
    map(function (entry) {return entry.path;})));};for (var i = 0; i < srcPaths.length; i++) {_loop(i);

  }
  return files;
}

/**
   * Given a src pattern and list of supported extensions, return a list of files to process
   * with this rule.
   * @param {string} src - file, directory, or glob pattern of files to act on
   * @param {string[]} extensions - list of supported file extensions
   * @param {import('eslint').Rule.RuleContext} context - the eslint context object
   * @returns {string[] | { filename: string, ignored: boolean }[]} the list of files that this rule will evaluate.
   */
function listFilesToProcess(src, extensions, context) {
  // If the context object has the new session functions, then prefer those
  // Otherwise, fallback to using the deprecated `FileEnumerator` for legacy support.
  // https://github.com/eslint/eslint/issues/18087
  if (
  context.session &&
  context.session.isFileIgnored &&
  context.session.isDirectoryIgnored)
  {
    return listFilesWithModernApi(src, extensions, context.session);
  }

  // Fallback to og FileEnumerator
  var FileEnumerator = requireFileEnumerator();

  // If we got the FileEnumerator, then let's go with that
  if (FileEnumerator) {
    return listFilesUsingFileEnumerator(FileEnumerator, src, extensions);
  }
  // If not, then we can try even older versions of this capability (listFilesToProcess)
  return listFilesWithLegacyFunctions(src, extensions);
}

var EXPORT_DEFAULT_DECLARATION = 'ExportDefaultDeclaration';
var EXPORT_NAMED_DECLARATION = 'ExportNamedDeclaration';
var EXPORT_ALL_DECLARATION = 'ExportAllDeclaration';
var IMPORT_DECLARATION = 'ImportDeclaration';
var IMPORT_NAMESPACE_SPECIFIER = 'ImportNamespaceSpecifier';
var IMPORT_DEFAULT_SPECIFIER = 'ImportDefaultSpecifier';
var VARIABLE_DECLARATION = 'VariableDeclaration';
var FUNCTION_DECLARATION = 'FunctionDeclaration';
var CLASS_DECLARATION = 'ClassDeclaration';
var IDENTIFIER = 'Identifier';
var OBJECT_PATTERN = 'ObjectPattern';
var ARRAY_PATTERN = 'ArrayPattern';
var TS_INTERFACE_DECLARATION = 'TSInterfaceDeclaration';
var TS_TYPE_ALIAS_DECLARATION = 'TSTypeAliasDeclaration';
var TS_ENUM_DECLARATION = 'TSEnumDeclaration';
var DEFAULT = 'default';

function forEachDeclarationIdentifier(declaration, cb) {
  if (declaration) {
    var isTypeDeclaration = declaration.type === TS_INTERFACE_DECLARATION ||
    declaration.type === TS_TYPE_ALIAS_DECLARATION ||
    declaration.type === TS_ENUM_DECLARATION;

    if (
    declaration.type === FUNCTION_DECLARATION ||
    declaration.type === CLASS_DECLARATION ||
    isTypeDeclaration)
    {
      cb(declaration.id.name, isTypeDeclaration);
    } else if (declaration.type === VARIABLE_DECLARATION) {
      declaration.declarations.forEach(function (_ref2) {var id = _ref2.id;
        if (id.type === OBJECT_PATTERN) {
          (0, _patternCapture2['default'])(id, function (pattern) {
            if (pattern.type === IDENTIFIER) {
              cb(pattern.name, false);
            }
          });
        } else if (id.type === ARRAY_PATTERN) {
          id.elements.forEach(function (_ref3) {var name = _ref3.name;
            cb(name, false);
          });
        } else {
          cb(id.name, false);
        }
      });
    }
  }
}

/**
   * List of imports per file.
   *
   * Represented by a two-level Map to a Set of identifiers. The upper-level Map
   * keys are the paths to the modules containing the imports, while the
   * lower-level Map keys are the paths to the files which are being imported
   * from. Lastly, the Set of identifiers contains either names being imported
   * or a special AST node name listed above (e.g ImportDefaultSpecifier).
   *
   * For example, if we have a file named foo.js containing:
   *
   *   import { o2 } from './bar.js';
   *
   * Then we will have a structure that looks like:
   *
   *   Map { 'foo.js' => Map { 'bar.js' => Set { 'o2' } } }
   *
   * @type {Map<string, Map<string, Set<string>>>}
   */
var importList = new Map();

/**
                             * List of exports per file.
                             *
                             * Represented by a two-level Map to an object of metadata. The upper-level Map
                             * keys are the paths to the modules containing the exports, while the
                             * lower-level Map keys are the specific identifiers or special AST node names
                             * being exported. The leaf-level metadata object at the moment only contains a
                             * `whereUsed` property, which contains a Set of paths to modules that import
                             * the name.
                             *
                             * For example, if we have a file named bar.js containing the following exports:
                             *
                             *   const o2 = 'bar';
                             *   export { o2 };
                             *
                             * And a file named foo.js containing the following import:
                             *
                             *   import { o2 } from './bar.js';
                             *
                             * Then we will have a structure that looks like:
                             *
                             *   Map { 'bar.js' => Map { 'o2' => { whereUsed: Set { 'foo.js' } } } }
                             *
                             * @type {Map<string, Map<string, object>>}
                             */
var exportList = new Map();

var visitorKeyMap = new Map();

/** @type {Set<string>} */
var ignoredFiles = new Set();
var filesOutsideSrc = new Set();

var isNodeModule = function isNodeModule(path) {return (/\/(node_modules)\//.test(path));};

/**
                                                                                             * read all files matching the patterns in src and ignoreExports
                                                                                             *
                                                                                             * return all files matching src pattern, which are not matching the ignoreExports pattern
                                                                                             * @type {(src: string, ignoreExports: string, context: import('eslint').Rule.RuleContext) => Set<string>}
                                                                                             */
function resolveFiles(src, ignoreExports, context) {
  var extensions = Array.from((0, _ignore.getFileExtensions)(context.settings));

  var srcFileList = listFilesToProcess(src, extensions, context);

  // prepare list of ignored files
  var ignoredFilesList = listFilesToProcess(ignoreExports, extensions, context);

  // The modern api will return a list of file paths, rather than an object
  if (ignoredFilesList.length && typeof ignoredFilesList[0] === 'string') {
    ignoredFilesList.forEach(function (filename) {return ignoredFiles.add(filename);});
  } else {
    ignoredFilesList.forEach(function (_ref4) {var filename = _ref4.filename;return ignoredFiles.add(filename);});
  }

  // prepare list of source files, don't consider files from node_modules
  var resolvedFiles = srcFileList.length && typeof srcFileList[0] === 'string' ?
  srcFileList.filter(function (filePath) {return !isNodeModule(filePath);}) :
  (0, _arrayPrototype2['default'])(srcFileList, function (_ref5) {var filename = _ref5.filename;return isNodeModule(filename) ? [] : filename;});

  return new Set(resolvedFiles);
}

/**
   * parse all source files and build up 2 maps containing the existing imports and exports
   */
var prepareImportsAndExports = function prepareImportsAndExports(srcFiles, context) {
  var exportAll = new Map();
  srcFiles.forEach(function (file) {
    var exports = new Map();
    var imports = new Map();
    var currentExports = _builder2['default'].get(file, context);
    if (currentExports) {var

      dependencies =




      currentExports.dependencies,reexports = currentExports.reexports,localImportList = currentExports.imports,namespace = currentExports.namespace,visitorKeys = currentExports.visitorKeys;

      visitorKeyMap.set(file, visitorKeys);
      // dependencies === export * from
      var currentExportAll = new Set();
      dependencies.forEach(function (getDependency) {
        var dependency = getDependency();
        if (dependency === null) {
          return;
        }

        currentExportAll.add(dependency.path);
      });
      exportAll.set(file, currentExportAll);

      reexports.forEach(function (value, key) {
        if (key === DEFAULT) {
          exports.set(IMPORT_DEFAULT_SPECIFIER, { whereUsed: new Set() });
        } else {
          exports.set(key, { whereUsed: new Set() });
        }
        var reexport = value.getImport();
        if (!reexport) {
          return;
        }
        var localImport = imports.get(reexport.path);
        var currentValue = void 0;
        if (value.local === DEFAULT) {
          currentValue = IMPORT_DEFAULT_SPECIFIER;
        } else {
          currentValue = value.local;
        }
        if (typeof localImport !== 'undefined') {
          localImport = new Set([].concat(_toConsumableArray(localImport), [currentValue]));
        } else {
          localImport = new Set([currentValue]);
        }
        imports.set(reexport.path, localImport);
      });

      localImportList.forEach(function (value, key) {
        if (isNodeModule(key)) {
          return;
        }
        var localImport = imports.get(key) || new Set();
        value.declarations.forEach(function (_ref6) {var importedSpecifiers = _ref6.importedSpecifiers;
          importedSpecifiers.forEach(function (specifier) {
            localImport.add(specifier);
          });
        });
        imports.set(key, localImport);
      });
      importList.set(file, imports);

      // build up export list only, if file is not ignored
      if (ignoredFiles.has(file)) {
        return;
      }
      namespace.forEach(function (value, key) {
        if (key === DEFAULT) {
          exports.set(IMPORT_DEFAULT_SPECIFIER, { whereUsed: new Set() });
        } else {
          exports.set(key, { whereUsed: new Set() });
        }
      });
    }
    exports.set(EXPORT_ALL_DECLARATION, { whereUsed: new Set() });
    exports.set(IMPORT_NAMESPACE_SPECIFIER, { whereUsed: new Set() });
    exportList.set(file, exports);
  });
  exportAll.forEach(function (value, key) {
    value.forEach(function (val) {
      var currentExports = exportList.get(val);
      if (currentExports) {
        var currentExport = currentExports.get(EXPORT_ALL_DECLARATION);
        currentExport.whereUsed.add(key);
      }
    });
  });
};

/**
    * traverse through all imports and add the respective path to the whereUsed-list
    * of the corresponding export
    */
var determineUsage = function determineUsage() {
  importList.forEach(function (listValue, listKey) {
    listValue.forEach(function (value, key) {
      var exports = exportList.get(key);
      if (typeof exports !== 'undefined') {
        value.forEach(function (currentImport) {
          var specifier = void 0;
          if (currentImport === IMPORT_NAMESPACE_SPECIFIER) {
            specifier = IMPORT_NAMESPACE_SPECIFIER;
          } else if (currentImport === IMPORT_DEFAULT_SPECIFIER) {
            specifier = IMPORT_DEFAULT_SPECIFIER;
          } else {
            specifier = currentImport;
          }
          if (typeof specifier !== 'undefined') {
            var exportStatement = exports.get(specifier);
            if (typeof exportStatement !== 'undefined') {var
              whereUsed = exportStatement.whereUsed;
              whereUsed.add(listKey);
              exports.set(specifier, { whereUsed: whereUsed });
            }
          }
        });
      }
    });
  });
};

var getSrc = function getSrc(src) {
  if (src) {
    return src;
  }
  return [process.cwd()];
};

/**
    * prepare the lists of existing imports and exports - should only be executed once at
    * the start of a new eslint run
    */
/** @type {Set<string>} */
var srcFiles = void 0;
var lastPrepareKey = void 0;
var doPreparation = function doPreparation(src, ignoreExports, context) {
  var prepareKey = JSON.stringify({
    src: (src || []).sort(),
    ignoreExports: (ignoreExports || []).sort(),
    extensions: Array.from((0, _ignore.getFileExtensions)(context.settings)).sort() });

  if (prepareKey === lastPrepareKey) {
    return;
  }

  importList.clear();
  exportList.clear();
  ignoredFiles.clear();
  filesOutsideSrc.clear();

  srcFiles = resolveFiles(getSrc(src), ignoreExports, context);
  prepareImportsAndExports(srcFiles, context);
  determineUsage();
  lastPrepareKey = prepareKey;
};

var newNamespaceImportExists = function newNamespaceImportExists(specifiers) {return specifiers.some(function (_ref7) {var type = _ref7.type;return type === IMPORT_NAMESPACE_SPECIFIER;});};

var newDefaultImportExists = function newDefaultImportExists(specifiers) {return specifiers.some(function (_ref8) {var type = _ref8.type;return type === IMPORT_DEFAULT_SPECIFIER;});};

var fileIsInPkg = function fileIsInPkg(file) {var _readPkgUp =
  (0, _readPkgUp3['default'])({ cwd: file }),path = _readPkgUp.path,pkg = _readPkgUp.pkg;
  var basePath = (0, _path.dirname)(path);

  var checkPkgFieldString = function checkPkgFieldString(pkgField) {
    if ((0, _path.join)(basePath, pkgField) === file) {
      return true;
    }
  };

  var checkPkgFieldObject = function checkPkgFieldObject(pkgField) {
    var pkgFieldFiles = (0, _arrayPrototype2['default'])((0, _object2['default'])(pkgField), function (value) {return typeof value === 'boolean' ? [] : (0, _path.join)(basePath, value);});

    if ((0, _arrayIncludes2['default'])(pkgFieldFiles, file)) {
      return true;
    }
  };

  var checkPkgField = function checkPkgField(pkgField) {
    if (typeof pkgField === 'string') {
      return checkPkgFieldString(pkgField);
    }

    if ((typeof pkgField === 'undefined' ? 'undefined' : _typeof(pkgField)) === 'object') {
      return checkPkgFieldObject(pkgField);
    }
  };

  if (pkg['private'] === true) {
    return false;
  }

  if (pkg.bin) {
    if (checkPkgField(pkg.bin)) {
      return true;
    }
  }

  if (pkg.browser) {
    if (checkPkgField(pkg.browser)) {
      return true;
    }
  }

  if (pkg.main) {
    if (checkPkgFieldString(pkg.main)) {
      return true;
    }
  }

  return false;
};

module.exports = {
  meta: {
    type: 'suggestion',
    docs: {
      category: 'Helpful warnings',
      description: 'Forbid modules without exports, or exports without matching import in another module.',
      url: (0, _docsUrl2['default'])('no-unused-modules') },

    schema: [{
      properties: {
        src: {
          description: 'files/paths to be analyzed (only for unused exports)',
          type: 'array',
          uniqueItems: true,
          items: {
            type: 'string',
            minLength: 1 } },


        ignoreExports: {
          description: 'files/paths for which unused exports will not be reported (e.g module entry points)',
          type: 'array',
          uniqueItems: true,
          items: {
            type: 'string',
            minLength: 1 } },


        missingExports: {
          description: 'report modules without any exports',
          type: 'boolean' },

        unusedExports: {
          description: 'report exports without any usage',
          type: 'boolean' },

        ignoreUnusedTypeExports: {
          description: 'ignore type exports without any usage',
          type: 'boolean' } },


      anyOf: [
      {
        properties: {
          unusedExports: { 'enum': [true] },
          src: {
            minItems: 1 } },


        required: ['unusedExports'] },

      {
        properties: {
          missingExports: { 'enum': [true] } },

        required: ['missingExports'] }] }] },





  create: function () {function create(context) {var _ref9 =






      context.options[0] || {},src = _ref9.src,_ref9$ignoreExports = _ref9.ignoreExports,ignoreExports = _ref9$ignoreExports === undefined ? [] : _ref9$ignoreExports,missingExports = _ref9.missingExports,unusedExports = _ref9.unusedExports,ignoreUnusedTypeExports = _ref9.ignoreUnusedTypeExports;

      if (unusedExports) {
        doPreparation(src, ignoreExports, context);
      }

      var file = (0, _contextCompat.getPhysicalFilename)(context);

      var checkExportPresence = function () {function checkExportPresence(node) {
          if (!missingExports) {
            return;
          }

          if (ignoredFiles.has(file)) {
            return;
          }

          var exportCount = exportList.get(file);
          var exportAll = exportCount.get(EXPORT_ALL_DECLARATION);
          var namespaceImports = exportCount.get(IMPORT_NAMESPACE_SPECIFIER);

          exportCount['delete'](EXPORT_ALL_DECLARATION);
          exportCount['delete'](IMPORT_NAMESPACE_SPECIFIER);
          if (exportCount.size < 1) {
            // node.body[0] === 'undefined' only happens, if everything is commented out in the file
            // being linted
            context.report(node.body[0] ? node.body[0] : node, 'No exports found');
          }
          exportCount.set(EXPORT_ALL_DECLARATION, exportAll);
          exportCount.set(IMPORT_NAMESPACE_SPECIFIER, namespaceImports);
        }return checkExportPresence;}();

      var checkUsage = function () {function checkUsage(node, exportedValue, isTypeExport) {
          if (!unusedExports) {
            return;
          }

          if (isTypeExport && ignoreUnusedTypeExports) {
            return;
          }

          if (ignoredFiles.has(file)) {
            return;
          }

          if (fileIsInPkg(file)) {
            return;
          }

          if (filesOutsideSrc.has(file)) {
            return;
          }

          // make sure file to be linted is included in source files
          if (!srcFiles.has(file)) {
            srcFiles = resolveFiles(getSrc(src), ignoreExports, context);
            if (!srcFiles.has(file)) {
              filesOutsideSrc.add(file);
              return;
            }
          }

          exports = exportList.get(file);

          if (!exports) {
            console.error('file `' + String(file) + '` has no exports. Please update to the latest, and if it still happens, report this on https://github.com/import-js/eslint-plugin-import/issues/2866!');
          }

          // special case: export * from
          var exportAll = exports.get(EXPORT_ALL_DECLARATION);
          if (typeof exportAll !== 'undefined' && exportedValue !== IMPORT_DEFAULT_SPECIFIER) {
            if (exportAll.whereUsed.size > 0) {
              return;
            }
          }

          // special case: namespace import
          var namespaceImports = exports.get(IMPORT_NAMESPACE_SPECIFIER);
          if (typeof namespaceImports !== 'undefined') {
            if (namespaceImports.whereUsed.size > 0) {
              return;
            }
          }

          // exportsList will always map any imported value of 'default' to 'ImportDefaultSpecifier'
          var exportsKey = exportedValue === DEFAULT ? IMPORT_DEFAULT_SPECIFIER : exportedValue;

          var exportStatement = exports.get(exportsKey);

          var value = exportsKey === IMPORT_DEFAULT_SPECIFIER ? DEFAULT : exportsKey;

          if (typeof exportStatement !== 'undefined') {
            if (exportStatement.whereUsed.size < 1) {
              context.report(
              node, 'exported declaration \'' +
              value + '\' not used within other modules');

            }
          } else {
            context.report(
            node, 'exported declaration \'' +
            value + '\' not used within other modules');

          }
        }return checkUsage;}();

      /**
                                 * only useful for tools like vscode-eslint
                                 *
                                 * update lists of existing exports during runtime
                                 */
      var updateExportUsage = function () {function updateExportUsage(node) {
          if (ignoredFiles.has(file)) {
            return;
          }

          var exports = exportList.get(file);

          // new module has been created during runtime
          // include it in further processing
          if (typeof exports === 'undefined') {
            exports = new Map();
          }

          var newExports = new Map();
          var newExportIdentifiers = new Set();

          node.body.forEach(function (_ref10) {var type = _ref10.type,declaration = _ref10.declaration,specifiers = _ref10.specifiers;
            if (type === EXPORT_DEFAULT_DECLARATION) {
              newExportIdentifiers.add(IMPORT_DEFAULT_SPECIFIER);
            }
            if (type === EXPORT_NAMED_DECLARATION) {
              if (specifiers.length > 0) {
                specifiers.forEach(function (specifier) {
                  if (specifier.exported) {
                    newExportIdentifiers.add(specifier.exported.name || specifier.exported.value);
                  }
                });
              }
              forEachDeclarationIdentifier(declaration, function (name) {
                newExportIdentifiers.add(name);
              });
            }
          });

          // old exports exist within list of new exports identifiers: add to map of new exports
          exports.forEach(function (value, key) {
            if (newExportIdentifiers.has(key)) {
              newExports.set(key, value);
            }
          });

          // new export identifiers added: add to map of new exports
          newExportIdentifiers.forEach(function (key) {
            if (!exports.has(key)) {
              newExports.set(key, { whereUsed: new Set() });
            }
          });

          // preserve information about namespace imports
          var exportAll = exports.get(EXPORT_ALL_DECLARATION);
          var namespaceImports = exports.get(IMPORT_NAMESPACE_SPECIFIER);

          if (typeof namespaceImports === 'undefined') {
            namespaceImports = { whereUsed: new Set() };
          }

          newExports.set(EXPORT_ALL_DECLARATION, exportAll);
          newExports.set(IMPORT_NAMESPACE_SPECIFIER, namespaceImports);
          exportList.set(file, newExports);
        }return updateExportUsage;}();

      /**
                                        * only useful for tools like vscode-eslint
                                        *
                                        * update lists of existing imports during runtime
                                        */
      var updateImportUsage = function () {function updateImportUsage(node) {
          if (!unusedExports) {
            return;
          }

          var oldImportPaths = importList.get(file);
          if (typeof oldImportPaths === 'undefined') {
            oldImportPaths = new Map();
          }

          var oldNamespaceImports = new Set();
          var newNamespaceImports = new Set();

          var oldExportAll = new Set();
          var newExportAll = new Set();

          var oldDefaultImports = new Set();
          var newDefaultImports = new Set();

          var oldImports = new Map();
          var newImports = new Map();
          oldImportPaths.forEach(function (value, key) {
            if (value.has(EXPORT_ALL_DECLARATION)) {
              oldExportAll.add(key);
            }
            if (value.has(IMPORT_NAMESPACE_SPECIFIER)) {
              oldNamespaceImports.add(key);
            }
            if (value.has(IMPORT_DEFAULT_SPECIFIER)) {
              oldDefaultImports.add(key);
            }
            value.forEach(function (val) {
              if (
              val !== IMPORT_NAMESPACE_SPECIFIER &&
              val !== IMPORT_DEFAULT_SPECIFIER)
              {
                oldImports.set(val, key);
              }
            });
          });

          function processDynamicImport(source) {
            if (source.type !== 'Literal') {
              return null;
            }
            var p = (0, _resolve2['default'])(source.value, context);
            if (p == null) {
              return null;
            }
            newNamespaceImports.add(p);
          }

          (0, _visit2['default'])(node, visitorKeyMap.get(file), {
            ImportExpression: function () {function ImportExpression(child) {
                processDynamicImport(child.source);
              }return ImportExpression;}(),
            CallExpression: function () {function CallExpression(child) {
                if (child.callee.type === 'Import') {
                  processDynamicImport(child.arguments[0]);
                }
              }return CallExpression;}() });


          node.body.forEach(function (astNode) {
            var resolvedPath = void 0;

            // support for export { value } from 'module'
            if (astNode.type === EXPORT_NAMED_DECLARATION) {
              if (astNode.source) {
                resolvedPath = (0, _resolve2['default'])(astNode.source.raw.replace(/('|")/g, ''), context);
                astNode.specifiers.forEach(function (specifier) {
                  var name = specifier.local.name || specifier.local.value;
                  if (name === DEFAULT) {
                    newDefaultImports.add(resolvedPath);
                  } else {
                    newImports.set(name, resolvedPath);
                  }
                });
              }
            }

            if (astNode.type === EXPORT_ALL_DECLARATION) {
              resolvedPath = (0, _resolve2['default'])(astNode.source.raw.replace(/('|")/g, ''), context);
              newExportAll.add(resolvedPath);
            }

            if (astNode.type === IMPORT_DECLARATION) {
              resolvedPath = (0, _resolve2['default'])(astNode.source.raw.replace(/('|")/g, ''), context);
              if (!resolvedPath) {
                return;
              }

              if (isNodeModule(resolvedPath)) {
                return;
              }

              if (newNamespaceImportExists(astNode.specifiers)) {
                newNamespaceImports.add(resolvedPath);
              }

              if (newDefaultImportExists(astNode.specifiers)) {
                newDefaultImports.add(resolvedPath);
              }

              astNode.specifiers.
              filter(function (specifier) {return specifier.type !== IMPORT_DEFAULT_SPECIFIER && specifier.type !== IMPORT_NAMESPACE_SPECIFIER;}).
              forEach(function (specifier) {
                newImports.set(specifier.imported.name || specifier.imported.value, resolvedPath);
              });
            }
          });

          newExportAll.forEach(function (value) {
            if (!oldExportAll.has(value)) {
              var imports = oldImportPaths.get(value);
              if (typeof imports === 'undefined') {
                imports = new Set();
              }
              imports.add(EXPORT_ALL_DECLARATION);
              oldImportPaths.set(value, imports);

              var _exports = exportList.get(value);
              var currentExport = void 0;
              if (typeof _exports !== 'undefined') {
                currentExport = _exports.get(EXPORT_ALL_DECLARATION);
              } else {
                _exports = new Map();
                exportList.set(value, _exports);
              }

              if (typeof currentExport !== 'undefined') {
                currentExport.whereUsed.add(file);
              } else {
                var whereUsed = new Set();
                whereUsed.add(file);
                _exports.set(EXPORT_ALL_DECLARATION, { whereUsed: whereUsed });
              }
            }
          });

          oldExportAll.forEach(function (value) {
            if (!newExportAll.has(value)) {
              var imports = oldImportPaths.get(value);
              imports['delete'](EXPORT_ALL_DECLARATION);

              var _exports2 = exportList.get(value);
              if (typeof _exports2 !== 'undefined') {
                var currentExport = _exports2.get(EXPORT_ALL_DECLARATION);
                if (typeof currentExport !== 'undefined') {
                  currentExport.whereUsed['delete'](file);
                }
              }
            }
          });

          newDefaultImports.forEach(function (value) {
            if (!oldDefaultImports.has(value)) {
              var imports = oldImportPaths.get(value);
              if (typeof imports === 'undefined') {
                imports = new Set();
              }
              imports.add(IMPORT_DEFAULT_SPECIFIER);
              oldImportPaths.set(value, imports);

              var _exports3 = exportList.get(value);
              var currentExport = void 0;
              if (typeof _exports3 !== 'undefined') {
                currentExport = _exports3.get(IMPORT_DEFAULT_SPECIFIER);
              } else {
                _exports3 = new Map();
                exportList.set(value, _exports3);
              }

              if (typeof currentExport !== 'undefined') {
                currentExport.whereUsed.add(file);
              } else {
                var whereUsed = new Set();
                whereUsed.add(file);
                _exports3.set(IMPORT_DEFAULT_SPECIFIER, { whereUsed: whereUsed });
              }
            }
          });

          oldDefaultImports.forEach(function (value) {
            if (!newDefaultImports.has(value)) {
              var imports = oldImportPaths.get(value);
              imports['delete'](IMPORT_DEFAULT_SPECIFIER);

              var _exports4 = exportList.get(value);
              if (typeof _exports4 !== 'undefined') {
                var currentExport = _exports4.get(IMPORT_DEFAULT_SPECIFIER);
                if (typeof currentExport !== 'undefined') {
                  currentExport.whereUsed['delete'](file);
                }
              }
            }
          });

          newNamespaceImports.forEach(function (value) {
            if (!oldNamespaceImports.has(value)) {
              var imports = oldImportPaths.get(value);
              if (typeof imports === 'undefined') {
                imports = new Set();
              }
              imports.add(IMPORT_NAMESPACE_SPECIFIER);
              oldImportPaths.set(value, imports);

              var _exports5 = exportList.get(value);
              var currentExport = void 0;
              if (typeof _exports5 !== 'undefined') {
                currentExport = _exports5.get(IMPORT_NAMESPACE_SPECIFIER);
              } else {
                _exports5 = new Map();
                exportList.set(value, _exports5);
              }

              if (typeof currentExport !== 'undefined') {
                currentExport.whereUsed.add(file);
              } else {
                var whereUsed = new Set();
                whereUsed.add(file);
                _exports5.set(IMPORT_NAMESPACE_SPECIFIER, { whereUsed: whereUsed });
              }
            }
          });

          oldNamespaceImports.forEach(function (value) {
            if (!newNamespaceImports.has(value)) {
              var imports = oldImportPaths.get(value);
              imports['delete'](IMPORT_NAMESPACE_SPECIFIER);

              var _exports6 = exportList.get(value);
              if (typeof _exports6 !== 'undefined') {
                var currentExport = _exports6.get(IMPORT_NAMESPACE_SPECIFIER);
                if (typeof currentExport !== 'undefined') {
                  currentExport.whereUsed['delete'](file);
                }
              }
            }
          });

          newImports.forEach(function (value, key) {
            if (!oldImports.has(key)) {
              var imports = oldImportPaths.get(value);
              if (typeof imports === 'undefined') {
                imports = new Set();
              }
              imports.add(key);
              oldImportPaths.set(value, imports);

              var _exports7 = exportList.get(value);
              var currentExport = void 0;
              if (typeof _exports7 !== 'undefined') {
                currentExport = _exports7.get(key);
              } else {
                _exports7 = new Map();
                exportList.set(value, _exports7);
              }

              if (typeof currentExport !== 'undefined') {
                currentExport.whereUsed.add(file);
              } else {
                var whereUsed = new Set();
                whereUsed.add(file);
                _exports7.set(key, { whereUsed: whereUsed });
              }
            }
          });

          oldImports.forEach(function (value, key) {
            if (!newImports.has(key)) {
              var imports = oldImportPaths.get(value);
              imports['delete'](key);

              var _exports8 = exportList.get(value);
              if (typeof _exports8 !== 'undefined') {
                var currentExport = _exports8.get(key);
                if (typeof currentExport !== 'undefined') {
                  currentExport.whereUsed['delete'](file);
                }
              }
            }
          });
        }return updateImportUsage;}();

      return {
        'Program:exit': function () {function ProgramExit(node) {
            updateExportUsage(node);
            updateImportUsage(node);
            checkExportPresence(node);
          }return ProgramExit;}(),
        ExportDefaultDeclaration: function () {function ExportDefaultDeclaration(node) {
            checkUsage(node, IMPORT_DEFAULT_SPECIFIER, false);
          }return ExportDefaultDeclaration;}(),
        ExportNamedDeclaration: function () {function ExportNamedDeclaration(node) {
            node.specifiers.forEach(function (specifier) {
              checkUsage(specifier, specifier.exported.name || specifier.exported.value, false);
            });
            forEachDeclarationIdentifier(node.declaration, function (name, isTypeExport) {
              checkUsage(node, name, isTypeExport);
            });
          }return ExportNamedDeclaration;}() };

    }return create;}() };
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIi4uLy4uL3NyYy9ydWxlcy9uby11bnVzZWQtbW9kdWxlcy5qcyJdLCJuYW1lcyI6WyJyZXF1aXJlRmlsZUVudW1lcmF0b3IiLCJGaWxlRW51bWVyYXRvciIsInJlcXVpcmUiLCJlIiwiY29kZSIsImxpc3RGaWxlc1VzaW5nRmlsZUVudW1lcmF0b3IiLCJzcmMiLCJleHRlbnNpb25zIiwiQXJyYXkiLCJmcm9tIiwiaXRlcmF0ZUZpbGVzIiwiZmlsZVBhdGgiLCJpZ25vcmVkIiwiZmlsZW5hbWUiLCJsaXN0RmlsZXNXaXRoTGVnYWN5RnVuY3Rpb25zIiwib3JpZ2luYWxMaXN0RmlsZXNUb1Byb2Nlc3MiLCJsaXN0RmlsZXNUb1Byb2Nlc3MiLCJwYXR0ZXJucyIsImNvbmNhdCIsInBhdHRlcm4iLCJtYXAiLCJleHRlbnNpb24iLCJ0ZXN0IiwibGlzdEZpbGVzV2l0aE1vZGVybkFwaSIsInNyY1BhdGhzIiwic2Vzc2lvbiIsImZpbGVzIiwiaSIsImVudHJpZXMiLCJkZWVwRmlsdGVyIiwiZW50cnkiLCJmdWxsRW50cnlQYXRoIiwicGF0aCIsImlzRGlyZWN0b3J5SWdub3JlZCIsImVudHJ5RmlsdGVyIiwiaXNGaWxlSWdub3JlZCIsImZpbmQiLCJlbmRzV2l0aCIsInB1c2giLCJmaWx0ZXIiLCJkaXJlbnQiLCJpc0RpcmVjdG9yeSIsImxlbmd0aCIsImNvbnRleHQiLCJFWFBPUlRfREVGQVVMVF9ERUNMQVJBVElPTiIsIkVYUE9SVF9OQU1FRF9ERUNMQVJBVElPTiIsIkVYUE9SVF9BTExfREVDTEFSQVRJT04iLCJJTVBPUlRfREVDTEFSQVRJT04iLCJJTVBPUlRfTkFNRVNQQUNFX1NQRUNJRklFUiIsIklNUE9SVF9ERUZBVUxUX1NQRUNJRklFUiIsIlZBUklBQkxFX0RFQ0xBUkFUSU9OIiwiRlVOQ1RJT05fREVDTEFSQVRJT04iLCJDTEFTU19ERUNMQVJBVElPTiIsIklERU5USUZJRVIiLCJPQkpFQ1RfUEFUVEVSTiIsIkFSUkFZX1BBVFRFUk4iLCJUU19JTlRFUkZBQ0VfREVDTEFSQVRJT04iLCJUU19UWVBFX0FMSUFTX0RFQ0xBUkFUSU9OIiwiVFNfRU5VTV9ERUNMQVJBVElPTiIsIkRFRkFVTFQiLCJmb3JFYWNoRGVjbGFyYXRpb25JZGVudGlmaWVyIiwiZGVjbGFyYXRpb24iLCJjYiIsImlzVHlwZURlY2xhcmF0aW9uIiwidHlwZSIsImlkIiwibmFtZSIsImRlY2xhcmF0aW9ucyIsImZvckVhY2giLCJlbGVtZW50cyIsImltcG9ydExpc3QiLCJNYXAiLCJleHBvcnRMaXN0IiwidmlzaXRvcktleU1hcCIsImlnbm9yZWRGaWxlcyIsIlNldCIsImZpbGVzT3V0c2lkZVNyYyIsImlzTm9kZU1vZHVsZSIsInJlc29sdmVGaWxlcyIsImlnbm9yZUV4cG9ydHMiLCJzZXR0aW5ncyIsInNyY0ZpbGVMaXN0IiwiaWdub3JlZEZpbGVzTGlzdCIsImFkZCIsInJlc29sdmVkRmlsZXMiLCJwcmVwYXJlSW1wb3J0c0FuZEV4cG9ydHMiLCJzcmNGaWxlcyIsImV4cG9ydEFsbCIsImZpbGUiLCJleHBvcnRzIiwiaW1wb3J0cyIsImN1cnJlbnRFeHBvcnRzIiwiRXhwb3J0TWFwQnVpbGRlciIsImdldCIsImRlcGVuZGVuY2llcyIsInJlZXhwb3J0cyIsImxvY2FsSW1wb3J0TGlzdCIsIm5hbWVzcGFjZSIsInZpc2l0b3JLZXlzIiwic2V0IiwiY3VycmVudEV4cG9ydEFsbCIsImdldERlcGVuZGVuY3kiLCJkZXBlbmRlbmN5IiwidmFsdWUiLCJrZXkiLCJ3aGVyZVVzZWQiLCJyZWV4cG9ydCIsImdldEltcG9ydCIsImxvY2FsSW1wb3J0IiwiY3VycmVudFZhbHVlIiwibG9jYWwiLCJpbXBvcnRlZFNwZWNpZmllcnMiLCJzcGVjaWZpZXIiLCJoYXMiLCJ2YWwiLCJjdXJyZW50RXhwb3J0IiwiZGV0ZXJtaW5lVXNhZ2UiLCJsaXN0VmFsdWUiLCJsaXN0S2V5IiwiY3VycmVudEltcG9ydCIsImV4cG9ydFN0YXRlbWVudCIsImdldFNyYyIsInByb2Nlc3MiLCJjd2QiLCJsYXN0UHJlcGFyZUtleSIsImRvUHJlcGFyYXRpb24iLCJwcmVwYXJlS2V5IiwiSlNPTiIsInN0cmluZ2lmeSIsInNvcnQiLCJjbGVhciIsIm5ld05hbWVzcGFjZUltcG9ydEV4aXN0cyIsInNwZWNpZmllcnMiLCJzb21lIiwibmV3RGVmYXVsdEltcG9ydEV4aXN0cyIsImZpbGVJc0luUGtnIiwicGtnIiwiYmFzZVBhdGgiLCJjaGVja1BrZ0ZpZWxkU3RyaW5nIiwicGtnRmllbGQiLCJjaGVja1BrZ0ZpZWxkT2JqZWN0IiwicGtnRmllbGRGaWxlcyIsImNoZWNrUGtnRmllbGQiLCJiaW4iLCJicm93c2VyIiwibWFpbiIsIm1vZHVsZSIsIm1ldGEiLCJkb2NzIiwiY2F0ZWdvcnkiLCJkZXNjcmlwdGlvbiIsInVybCIsInNjaGVtYSIsInByb3BlcnRpZXMiLCJ1bmlxdWVJdGVtcyIsIml0ZW1zIiwibWluTGVuZ3RoIiwibWlzc2luZ0V4cG9ydHMiLCJ1bnVzZWRFeHBvcnRzIiwiaWdub3JlVW51c2VkVHlwZUV4cG9ydHMiLCJhbnlPZiIsIm1pbkl0ZW1zIiwicmVxdWlyZWQiLCJjcmVhdGUiLCJvcHRpb25zIiwiY2hlY2tFeHBvcnRQcmVzZW5jZSIsIm5vZGUiLCJleHBvcnRDb3VudCIsIm5hbWVzcGFjZUltcG9ydHMiLCJzaXplIiwicmVwb3J0IiwiYm9keSIsImNoZWNrVXNhZ2UiLCJleHBvcnRlZFZhbHVlIiwiaXNUeXBlRXhwb3J0IiwiY29uc29sZSIsImVycm9yIiwiZXhwb3J0c0tleSIsInVwZGF0ZUV4cG9ydFVzYWdlIiwibmV3RXhwb3J0cyIsIm5ld0V4cG9ydElkZW50aWZpZXJzIiwiZXhwb3J0ZWQiLCJ1cGRhdGVJbXBvcnRVc2FnZSIsIm9sZEltcG9ydFBhdGhzIiwib2xkTmFtZXNwYWNlSW1wb3J0cyIsIm5ld05hbWVzcGFjZUltcG9ydHMiLCJvbGRFeHBvcnRBbGwiLCJuZXdFeHBvcnRBbGwiLCJvbGREZWZhdWx0SW1wb3J0cyIsIm5ld0RlZmF1bHRJbXBvcnRzIiwib2xkSW1wb3J0cyIsIm5ld0ltcG9ydHMiLCJwcm9jZXNzRHluYW1pY0ltcG9ydCIsInNvdXJjZSIsInAiLCJJbXBvcnRFeHByZXNzaW9uIiwiY2hpbGQiLCJDYWxsRXhwcmVzc2lvbiIsImNhbGxlZSIsImFyZ3VtZW50cyIsImFzdE5vZGUiLCJyZXNvbHZlZFBhdGgiLCJyYXciLCJyZXBsYWNlIiwiaW1wb3J0ZWQiLCJFeHBvcnREZWZhdWx0RGVjbGFyYXRpb24iLCJFeHBvcnROYW1lZERlY2xhcmF0aW9uIl0sIm1hcHBpbmdzIjoiOzs7Ozs7QUFNQTtBQUNBO0FBQ0Esc0Q7QUFDQSxrRDtBQUNBO0FBQ0EsMkQ7QUFDQSx1QztBQUNBLCtDO0FBQ0EseUQ7O0FBRUE7QUFDQSwrQztBQUNBLDZEO0FBQ0EscUMsMlVBbkJBOzs7O29YQXFCQTs7Ozs7dVhBTUEsU0FBU0EscUJBQVQsR0FBaUMsQ0FDL0IsSUFBSUMsdUJBQUo7O0FBRUE7QUFDQSxNQUFJO0FBQ29CQyxZQUFRLDZCQUFSLENBRHBCLENBQ0NELGNBREQsWUFDQ0EsY0FERDtBQUVILEdBRkQsQ0FFRSxPQUFPRSxDQUFQLEVBQVU7QUFDVjtBQUNBLFFBQUlBLEVBQUVDLElBQUYsS0FBVyxrQkFBZixFQUFtQztBQUNqQyxZQUFNRCxDQUFOO0FBQ0Q7O0FBRUQ7QUFDQSxRQUFJO0FBQ29CRCxjQUFRLHVDQUFSLENBRHBCLENBQ0NELGNBREQsYUFDQ0EsY0FERDtBQUVILEtBRkQsQ0FFRSxPQUFPRSxDQUFQLEVBQVU7QUFDVjtBQUNBLFVBQUlBLEVBQUVDLElBQUYsS0FBVyxrQkFBZixFQUFtQztBQUNqQyxjQUFNRCxDQUFOO0FBQ0Q7QUFDRjtBQUNGO0FBQ0QsU0FBT0YsY0FBUDtBQUNEOztBQUVEOzs7Ozs7O0FBT0EsU0FBU0ksNEJBQVQsQ0FBc0NKLGNBQXRDLEVBQXNESyxHQUF0RCxFQUEyREMsVUFBM0QsRUFBdUU7QUFDckUsTUFBTUosSUFBSSxJQUFJRixjQUFKLENBQW1CO0FBQzNCTSwwQkFEMkIsRUFBbkIsQ0FBVjs7O0FBSUEsU0FBT0MsTUFBTUMsSUFBTjtBQUNMTixJ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NkIwRyxLQUFLekcsV0FBbEMsRUFBK0MsVUFBQ0ssSUFBRCxFQUFPNEcsWUFBUCxFQUF3QjtBQUNyRUYseUJBQVdOLElBQVgsRUFBaUJwRyxJQUFqQixFQUF1QjRHLFlBQXZCO0FBQ0QsYUFGRDtBQUdELFdBaEJJLG1DQUFQOztBQWtCRCxLQXBpQmMsbUJBQWpCIiwiZmlsZSI6Im5vLXVudXNlZC1tb2R1bGVzLmpzIiwic291cmNlc0NvbnRlbnQiOlsiLyoqXG4gKiBAZmlsZU92ZXJ2aWV3IEVuc3VyZXMgdGhhdCBtb2R1bGVzIGNvbnRhaW4gZXhwb3J0cyBhbmQvb3IgYWxsXG4gKiBtb2R1bGVzIGFyZSBjb25zdW1lZCB3aXRoaW4gb3RoZXIgbW9kdWxlcy5cbiAqIEBhdXRob3IgUmVuw6kgRmVybWFublxuICovXG5cbmltcG9ydCB7IGdldFBoeXNpY2FsRmlsZW5hbWUgfSBmcm9tICdlc2xpbnQtbW9kdWxlLXV0aWxzL2NvbnRleHRDb21wYXQnO1xuaW1wb3J0IHsgZ2V0RmlsZUV4dGVuc2lvbnMgfSBmcm9tICdlc2xpbnQtbW9kdWxlLXV0aWxzL2lnbm9yZSc7XG5pbXBvcnQgcmVzb2x2ZSBmcm9tICdlc2xpbnQtbW9kdWxlLXV0aWxzL3Jlc29sdmUnO1xuaW1wb3J0IHZpc2l0IGZyb20gJ2VzbGludC1tb2R1bGUtdXRpbHMvdmlzaXQnO1xuaW1wb3J0IHsgZGlybmFtZSwgam9pbiwgcmVzb2x2ZSBhcyByZXNvbHZlUGF0aCB9IGZyb20gJ3BhdGgnO1xuaW1wb3J0IHJlYWRQa2dVcCBmcm9tICdlc2xpbnQtbW9kdWxlLXV0aWxzL3JlYWRQa2dVcCc7XG5pbXBvcnQgdmFsdWVzIGZyb20gJ29iamVjdC52YWx1ZXMnO1xuaW1wb3J0IGluY2x1ZGVzIGZyb20gJ2FycmF5LWluY2x1ZGVzJztcbmltcG9ydCBmbGF0TWFwIGZyb20gJ2FycmF5LnByb3RvdHlwZS5mbGF0bWFwJztcblxuaW1wb3J0IHsgd2Fsa1N5bmMgfSBmcm9tICcuLi9jb3JlL2ZzV2Fsayc7XG5pbXBvcnQgRXhwb3J0TWFwQnVpbGRlciBmcm9tICcuLi9leHBvcnRNYXAvYnVpbGRlcic7XG5pbXBvcnQgcmVjdXJzaXZlUGF0dGVybkNhcHR1cmUgZnJvbSAnLi4vZXhwb3J0TWFwL3BhdHRlcm5DYXB0dXJlJztcbmltcG9ydCBkb2NzVXJsIGZyb20gJy4uL2RvY3NVcmwnO1xuXG4vKipcbiAqIEF0dGVtcHQgdG8gbG9hZCB0aGUgaW50ZXJuYWwgYEZpbGVFbnVtZXJhdG9yYCBjbGFzcywgd2hpY2ggaGFzIGV4aXN0ZWQgaW4gYSBjb3VwbGVcbiAqIG9mIGRpZmZlcmVudCBwbGFjZXMsIGRlcGVuZGluZyBvbiB0aGUgdmVyc2lvbiBvZiBgZXNsaW50YC4gIFRyeSByZXF1aXJpbmcgaXQgZnJvbSBib3RoXG4gKiBsb2NhdGlvbnMuXG4gKiBAcmV0dXJucyBSZXR1cm5zIHRoZSBgRmlsZUVudW1lcmF0b3JgIGNsYXNzIGlmIGl0cyByZXF1aXJhYmxlLCBvdGhlcndpc2UgYHVuZGVmaW5lZGAuXG4gKi9cbmZ1bmN0aW9uIHJlcXVpcmVGaWxlRW51bWVyYXRvcigpIHtcbiAgbGV0IEZpbGVFbnVtZXJhdG9yO1xuXG4gIC8vIFRyeSBnZXR0aW5nIGl0IGZyb20gdGhlIGVzbGludCBwcml2YXRlIC8gZGVwcmVjYXRlZCBhcGlcbiAgdHJ5IHtcbiAgICAoeyBGaWxlRW51bWVyYXRvciB9ID0gcmVxdWlyZSgnZXNsaW50L3VzZS1hdC15b3VyLW93bi1yaXNrJykpO1xuICB9IGNhdGNoIChlKSB7XG4gICAgLy8gQWJzb3JiIHRoaXMgaWYgaXQncyBNT0RVTEVfTk9UX0ZPVU5EXG4gICAgaWYgKGUuY29kZSAhPT0gJ01PRFVMRV9OT1RfRk9VTkQnKSB7XG4gICAgICB0aHJvdyBlO1xuICAgIH1cblxuICAgIC8vIElmIG5vdCB0aGVyZSwgdGhlbiB0cnkgZ2V0dGluZyBpdCBmcm9tIGVzbGludC9saWIvY2xpLWVuZ2luZS9maWxlLWVudW1lcmF0b3IgKG1vdmVkIHRoZXJlIGluIHY2KVxuICAgIHRyeSB7XG4gICAgICAoeyBGaWxlRW51bWVyYXRvciB9ID0gcmVxdWlyZSgnZXNsaW50L2xpYi9jbGktZW5naW5lL2ZpbGUtZW51bWVyYXRvcicpKTtcbiAgICB9IGNhdGNoIChlKSB7XG4gICAgICAvLyBBYnNvcmIgdGhpcyBpZiBpdCdzIE1PRFVMRV9OT1RfRk9VTkRcbiAgICAgIGlmIChlLmNvZGUgIT09ICdNT0RVTEVfTk9UX0ZPVU5EJykge1xuICAgICAgICB0aHJvdyBlO1xuICAgICAgfVxuICAgIH1cbiAgfVxuICByZXR1cm4gRmlsZUVudW1lcmF0b3I7XG59XG5cbi8qKlxuICpcbiAqIEBwYXJhbSBGaWxlRW51bWVyYXRvciB0aGUgYEZpbGVFbnVtZXJhdG9yYCBjbGFzcyBmcm9tIGBlc2xpbnRgJ3MgaW50ZXJuYWwgYXBpXG4gKiBAcGFyYW0ge3N0cmluZ30gc3JjIHBhdGggdG8gdGhlIHNyYyByb290XG4gKiBAcGFyYW0ge3N0cmluZ1tdfSBleHRlbnNpb25zIGxpc3Qgb2Ygc3VwcG9ydGVkIGV4dGVuc2lvbnNcbiAqIEByZXR1cm5zIHt7IGZpbGVuYW1lOiBzdHJpbmcsIGlnbm9yZWQ6IGJvb2xlYW4gfVtdfSBsaXN0IG9mIGZpbGVzIHRvIG9wZXJhdGUgb25cbiAqL1xuZnVuY3Rpb24gbGlzdEZpbGVzVXNpbmdGaWxlRW51bWVyYXRvcihGaWxlRW51bWVyYXRvciwgc3JjLCBleHRlbnNpb25zKSB7XG4gIGNvbnN0IGUgPSBuZXcgRmlsZUVudW1lcmF0b3Ioe1xuICAgIGV4dGVuc2lvbnMsXG4gIH0pO1xuXG4gIHJldHVybiBBcnJheS5mcm9tKFxuICAgIGUuaXRlcmF0ZUZpbGVzKHNyYyksXG4gICAgKHsgZmlsZVBhdGgsIGlnbm9yZWQgfSkgPT4gKHsgZmlsZW5hbWU6IGZpbGVQYXRoLCBpZ25vcmVkIH0pLFxuICApO1xufVxuXG4vKipcbiAqIEF0dGVtcHQgdG8gcmVxdWlyZSBvbGQgdmVyc2lvbnMgb2YgdGhlIGZpbGUgZW51bWVyYXRpb24gY2FwYWJpbGl0eSBmcm9tIHY2IGBlc2xpbnRgIGFuZCBlYXJsaWVyLCBhbmQgdXNlXG4gKiB0aG9zZSBmdW5jdGlvbnMgdG8gcHJvdmlkZSB0aGUgbGlzdCBvZiBmaWxlcyB0byBvcGVyYXRlIG9uXG4gKiBAcGFyYW0ge3N0cmluZ30gc3JjIHBhdGggdG8gdGhlIHNyYyByb290XG4gKiBAcGFyYW0ge3N0cmluZ1tdfSBleHRlbnNpb25zIGxpc3Qgb2Ygc3VwcG9ydGVkIGV4dGVuc2lvbnNcbiAqIEByZXR1cm5zIHtzdHJpbmdbXX0gbGlzdCBvZiBmaWxlcyB0byBvcGVyYXRlIG9uXG4gKi9cbmZ1bmN0aW9uIGxpc3RGaWxlc1dpdGhMZWdhY3lGdW5jdGlvbnMoc3JjLCBleHRlbnNpb25zKSB7XG4gIHRyeSB7XG4gICAgLy8gZXNsaW50L2xpYi91dGlsL2dsb2ItdXRpbCBoYXMgYmVlbiBtb3ZlZCB0byBlc2xpbnQvbGliL3V0aWwvZ2xvYi11dGlscyB3aXRoIHZlcnNpb24gNS4zXG4gICAgY29uc3QgeyBsaXN0RmlsZXNUb1Byb2Nlc3M6IG9yaWdpbmFsTGlzdEZpbGVzVG9Qcm9jZXNzIH0gPSByZXF1aXJlKCdlc2xpbnQvbGliL3V0aWwvZ2xvYi11dGlscycpO1xuICAgIC8vIFByZXZlbnQgcGFzc2luZyBpbnZhbGlkIG9wdGlvbnMgKGV4dGVuc2lvbnMgYXJyYXkpIHRvIG9sZCB2ZXJzaW9ucyBvZiB0aGUgZnVuY3Rpb24uXG4gICAgLy8gaHR0cHM6Ly9naXRodWIuY29tL2VzbGludC9lc2xpbnQvYmxvYi92NS4xNi4wL2xpYi91dGlsL2dsb2ItdXRpbHMuanMjTDE3OC1MMjgwXG4gICAgLy8gaHR0cHM6Ly9naXRodWIuY29tL2VzbGludC9lc2xpbnQvYmxvYi92NS4yLjAvbGliL3V0aWwvZ2xvYi11dGlsLmpzI0wxNzQtTDI2OVxuXG4gICAgcmV0dXJuIG9yaWdpbmFsTGlzdEZpbGVzVG9Qcm9jZXNzKHNyYywge1xuICAgICAgZXh0ZW5zaW9ucyxcbiAgICB9KTtcbiAgfSBjYXRjaCAoZSkge1xuICAgIC8vIEFic29yYiB0aGlzIGlmIGl0J3MgTU9EVUxFX05PVF9GT1VORFxuICAgIGlmIChlLmNvZGUgIT09ICdNT0RVTEVfTk9UX0ZPVU5EJykge1xuICAgICAgdGhyb3cgZTtcbiAgICB9XG5cbiAgICAvLyBMYXN0IHBsYWNlIHRvIHRyeSAocHJlIHY1LjMpXG4gICAgY29uc3Qge1xuICAgICAgbGlzdEZpbGVzVG9Qcm9jZXNzOiBvcmlnaW5hbExpc3RGaWxlc1RvUHJvY2VzcyxcbiAgICB9ID0gcmVxdWlyZSgnZXNsaW50L2xpYi91dGlsL2dsb2ItdXRpbCcpO1xuICAgIGNvbnN0IHBhdHRlcm5zID0gc3JjLmNvbmNhdChcbiAgICAgIGZsYXRNYXAoXG4gICAgICAgIHNyYyxcbiAgICAgICAgKHBhdHRlcm4pID0+IGV4dGVuc2lvbnMubWFwKChleHRlbnNpb24pID0+ICgvXFwqXFwqfFxcKlxcLi8pLnRlc3QocGF0dGVybikgPyBwYXR0ZXJuIDogYCR7cGF0dGVybn0vKiovKiR7ZXh0ZW5zaW9ufWApLFxuICAgICAgKSxcbiAgICApO1xuXG4gICAgcmV0dXJuIG9yaWdpbmFsTGlzdEZpbGVzVG9Qcm9jZXNzKHBhdHRlcm5zKTtcbiAgfVxufVxuXG4vKipcbiAqIEdpdmVuIGEgc291cmNlIHJvb3QgYW5kIGxpc3Qgb2Ygc3VwcG9ydGVkIGV4dGVuc2lvbnMsIHVzZSBmc1dhbGsgYW5kIHRoZVxuICogbmV3IGBlc2xpbnRgIGBjb250ZXh0LnNlc3Npb25gIGFwaSB0byBidWlsZCB0aGUgbGlzdCBvZiBmaWxlcyB3ZSB3YW50IHRvIG9wZXJhdGUgb25cbiAqIEBwYXJhbSB7c3RyaW5nW119IHNyY1BhdGhzIGFycmF5IG9mIHNvdXJjZSBwYXRocyAoZm9yIGZsYXQgY29uZmlnIHRoaXMgc2hvdWxkIGp1c3QgYmUgYSBzaW5ndWxhciByb290IChlLmcuIGN3ZCkpXG4gKiBAcGFyYW0ge3N0cmluZ1tdfSBleHRlbnNpb25zIGxpc3Qgb2Ygc3VwcG9ydGVkIGV4dGVuc2lvbnNcbiAqIEBwYXJhbSB7eyBpc0RpcmVjdG9yeUlnbm9yZWQ6IChwYXRoOiBzdHJpbmcpID0+IGJvb2xlYW4sIGlzRmlsZUlnbm9yZWQ6IChwYXRoOiBzdHJpbmcpID0+IGJvb2xlYW4gfX0gc2Vzc2lvbiBlc2xpbnQgY29udGV4dCBzZXNzaW9uIG9iamVjdFxuICogQHJldHVybnMge3N0cmluZ1tdfSBsaXN0IG9mIGZpbGVzIHRvIG9wZXJhdGUgb25cbiAqL1xuZnVuY3Rpb24gbGlzdEZpbGVzV2l0aE1vZGVybkFwaShzcmNQYXRocywgZXh0ZW5zaW9ucywgc2Vzc2lvbikge1xuICAvKiogQHR5cGUge3N0cmluZ1tdfSAqL1xuICBjb25zdCBmaWxlcyA9IFtdO1xuXG4gIGZvciAobGV0IGkgPSAwOyBpIDwgc3JjUGF0aHMubGVuZ3RoOyBpKyspIHtcbiAgICBjb25zdCBzcmMgPSBzcmNQYXRoc1tpXTtcbiAgICAvLyBVc2Ugd2Fsa1N5bmMgYWxvbmcgd2l0aCB0aGUgbmV3IHNlc3Npb24gYXBpIHRvIGdhdGhlciB0aGUgbGlzdCBvZiBmaWxlc1xuICAgIGNvbnN0IGVudHJpZXMgPSB3YWxrU3luYyhzcmMsIHtcbiAgICAgIGRlZXBGaWx0ZXIoZW50cnkpIHtcbiAgICAgICAgY29uc3QgZnVsbEVudHJ5UGF0aCA9IHJlc29sdmVQYXRoKHNyYywgZW50cnkucGF0aCk7XG5cbiAgICAgICAgLy8gSW5jbHVkZSB0aGUgZGlyZWN0b3J5IGlmIGl0J3Mgbm90IG1hcmtlZCBhcyBpZ25vcmUgYnkgZXNsaW50XG4gICAgICAgIHJldHVybiAhc2Vzc2lvbi5pc0RpcmVjdG9yeUlnbm9yZWQoZnVsbEVudHJ5UGF0aCk7XG4gICAgICB9LFxuICAgICAgZW50cnlGaWx0ZXIoZW50cnkpIHtcbiAgICAgICAgY29uc3QgZnVsbEVudHJ5UGF0aCA9IHJlc29sdmVQYXRoKHNyYywgZW50cnkucGF0aCk7XG5cbiAgICAgICAgLy8gSW5jbHVkZSB0aGUgZmlsZSBpZiBpdCdzIG5vdCBtYXJrZWQgYXMgaWdub3JlIGJ5IGVzbGludCBhbmQgaXRzIGV4dGVuc2lvbiBpcyBpbmNsdWRlZCBpbiBvdXIgbGlzdFxuICAgICAgICByZXR1cm4gKFxuICAgICAgICAgICFzZXNzaW9uLmlzRmlsZUlnbm9yZWQoZnVsbEVudHJ5UGF0aClcbiAgICAgICAgICAmJiBleHRlbnNpb25zLmZpbmQoKGV4dGVuc2lvbikgPT4gZW50cnkucGF0aC5lbmRzV2l0aChleHRlbnNpb24pKVxuICAgICAgICApO1xuICAgICAgfSxcbiAgICB9KTtcblxuICAgIC8vIEZpbHRlciBvdXQgZGlyZWN0b3JpZXMgYW5kIG1hcCBlbnRyaWVzIHRvIHRoZWlyIHBhdGhzXG4gICAgZmlsZXMucHVzaChcbiAgICAgIC4uLmVudHJpZXNcbiAgICAgICAgLmZpbHRlcigoZW50cnkpID0+ICFlbnRyeS5kaXJlbnQuaXNEaXJlY3RvcnkoKSlcbiAgICAgICAgLm1hcCgoZW50cnkpID0+IGVudHJ5LnBhdGgpLFxuICAgICk7XG4gIH1cbiAgcmV0dXJuIGZpbGVzO1xufVxuXG4vKipcbiAqIEdpdmVuIGEgc3JjIHBhdHRlcm4gYW5kIGxpc3Qgb2Ygc3VwcG9ydGVkIGV4dGVuc2lvbnMsIHJldHVybiBhIGxpc3Qgb2YgZmlsZXMgdG8gcHJvY2Vzc1xuICogd2l0aCB0aGlzIHJ1bGUuXG4gKiBAcGFyYW0ge3N0cmluZ30gc3JjIC0gZmlsZSwgZGlyZWN0b3J5LCBvciBnbG9iIHBhdHRlcm4gb2YgZmlsZXMgdG8gYWN0IG9uXG4gKiBAcGFyYW0ge3N0cmluZ1tdfSBleHRlbnNpb25zIC0gbGlzdCBvZiBzdXBwb3J0ZWQgZmlsZSBleHRlbnNpb25zXG4gKiBAcGFyYW0ge2ltcG9ydCgnZXNsaW50JykuUnVsZS5SdWxlQ29udGV4dH0gY29udGV4dCAtIHRoZSBlc2xpbnQgY29udGV4dCBvYmplY3RcbiAqIEByZXR1cm5zIHtzdHJpbmdbXSB8IHsgZmlsZW5hbWU6IHN0cmluZywgaWdub3JlZDogYm9vbGVhbiB9W119IHRoZSBsaXN0IG9mIGZpbGVzIHRoYXQgdGhpcyBydWxlIHdpbGwgZXZhbHVhdGUuXG4gKi9cbmZ1bmN0aW9uIGxpc3RGaWxlc1RvUHJvY2VzcyhzcmMsIGV4dGVuc2lvbnMsIGNvbnRleHQpIHtcbiAgLy8gSWYgdGhlIGNvbnRleHQgb2JqZWN0IGhhcyB0aGUgbmV3IHNlc3Npb24gZnVuY3Rpb25zLCB0aGVuIHByZWZlciB0aG9zZVxuICAvLyBPdGhlcndpc2UsIGZhbGxiYWNrIHRvIHVzaW5nIHRoZSBkZXByZWNhdGVkIGBGaWxlRW51bWVyYXRvcmAgZm9yIGxlZ2FjeSBzdXBwb3J0LlxuICAvLyBodHRwczovL2dpdGh1Yi5jb20vZXNsaW50L2VzbGludC9pc3N1ZXMvMTgwODdcbiAgaWYgKFxuICAgIGNvbnRleHQuc2Vzc2lvblxuICAgICYmIGNvbnRleHQuc2Vzc2lvbi5pc0ZpbGVJZ25vcmVkXG4gICAgJiYgY29udGV4dC5zZXNzaW9uLmlzRGlyZWN0b3J5SWdub3JlZFxuICApIHtcbiAgICByZXR1cm4gbGlzdEZpbGVzV2l0aE1vZGVybkFwaShzcmMsIGV4dGVuc2lvbnMsIGNvbnRleHQuc2Vzc2lvbik7XG4gIH1cblxuICAvLyBGYWxsYmFjayB0byBvZyBGaWxlRW51bWVyYXRvclxuICBjb25zdCBGaWxlRW51bWVyYXRvciA9IHJlcXVpcmVGaWxlRW51bWVyYXRvcigpO1xuXG4gIC8vIElmIHdlIGdvdCB0aGUgRmlsZUVudW1lcmF0b3IsIHRoZW4gbGV0J3MgZ28gd2l0aCB0aGF0XG4gIGlmIChGaWxlRW51bWVyYXRvcikge1xuICAgIHJldHVybiBsaXN0RmlsZXNVc2luZ0ZpbGVFbnVtZXJhdG9yKEZpbGVFbnVtZXJhdG9yLCBzcmMsIGV4dGVuc2lvbnMpO1xuICB9XG4gIC8vIElmIG5vdCwgdGhlbiB3ZSBjYW4gdHJ5IGV2ZW4gb2xkZXIgdmVyc2lvbnMgb2YgdGhpcyBjYXBhYmlsaXR5IChsaXN0RmlsZXNUb1Byb2Nlc3MpXG4gIHJldHVybiBsaXN0RmlsZXNXaXRoTGVnYWN5RnVuY3Rpb25zKHNyYywgZXh0ZW5zaW9ucyk7XG59XG5cbmNvbnN0IEVYUE9SVF9ERUZBVUxUX0RFQ0xBUkFUSU9OID0gJ0V4cG9ydERlZmF1bHREZWNsYXJhdGlvbic7XG5jb25zdCBFWFBPUlRfTkFNRURfREVDTEFSQVRJT04gPSAnRXhwb3J0TmFtZWREZWNsYXJhdGlvbic7XG5jb25zdCBFWFBPUlRfQUxMX0RFQ0xBUkFUSU9OID0gJ0V4cG9ydEFsbERlY2xhcmF0aW9uJztcbmNvbnN0IElNUE9SVF9ERUNMQVJBVElPTiA9ICdJbXBvcnREZWNsYXJhdGlvbic7XG5jb25zdCBJTVBPUlRfTkFNRVNQQUNFX1NQRUNJRklFUiA9ICdJbXBvcnROYW1lc3BhY2VTcGVjaWZpZXInO1xuY29uc3QgSU1QT1JUX0RFRkFVTFRfU1BFQ0lGSUVSID0gJ0ltcG9ydERlZmF1bHRTcGVjaWZpZXInO1xuY29uc3QgVkFSSUFCTEVfREVDTEFSQVRJT04gPSAnVmFyaWFibGVEZWNsYXJhdGlvbic7XG5jb25zdCBGVU5DVElPTl9ERUNMQVJBVElPTiA9ICdGdW5jdGlvbkRlY2xhcmF0aW9uJztcbmNvbnN0IENMQVNTX0RFQ0xBUkFUSU9OID0gJ0NsYXNzRGVjbGFyYXRpb24nO1xuY29uc3QgSURFTlRJRklFUiA9ICdJZGVudGlmaWVyJztcbmNvbnN0IE9CSkVDVF9QQVRURVJOID0gJ09iamVjdFBhdHRlcm4nO1xuY29uc3QgQVJSQVlfUEFUVEVSTiA9ICdBcnJheVBhdHRlcm4nO1xuY29uc3QgVFNfSU5URVJGQUNFX0RFQ0xBUkFUSU9OID0gJ1RTSW50ZXJmYWNlRGVjbGFyYXRpb24nO1xuY29uc3QgVFNfVFlQRV9BTElBU19ERUNMQVJBVElPTiA9ICdUU1R5cGVBbGlhc0RlY2xhcmF0aW9uJztcbmNvbnN0IFRTX0VOVU1fREVDTEFSQVRJT04gPSAnVFNFbnVtRGVjbGFyYXRpb24nO1xuY29uc3QgREVGQVVMVCA9ICdkZWZhdWx0JztcblxuZnVuY3Rpb24gZm9yRWFjaERlY2xhcmF0aW9uSWRlbnRpZmllcihkZWNsYXJhdGlvbiwgY2IpIHtcbiAgaWYgKGRlY2xhcmF0aW9uKSB7XG4gICAgY29uc3QgaXNUeXBlRGVjbGFyYXRpb24gPSBkZWNsYXJhdGlvbi50eXBlID09PSBUU19JTlRFUkZBQ0VfREVDTEFSQVRJT05cbiAgICAgIHx8IGRlY2xhcmF0aW9uLnR5cGUgPT09IFRTX1RZUEVfQUxJQVNfREVDTEFSQVRJT05cbiAgICAgIHx8IGRlY2xhcmF0aW9uLnR5cGUgPT09IFRTX0VOVU1fREVDTEFSQVRJT047XG5cbiAgICBpZiAoXG4gICAgICBkZWNsYXJhdGlvbi50eXBlID09PSBGVU5DVElPTl9ERUNMQVJBVElPTlxuICAgICAgfHwgZGVjbGFyYXRpb24udHlwZSA9PT0gQ0xBU1NfREVDTEFSQVRJT05cbiAgICAgIHx8IGlzVHlwZURlY2xhcmF0aW9uXG4gICAgKSB7XG4gICAgICBjYihkZWNsYXJhdGlvbi5pZC5uYW1lLCBpc1R5cGVEZWNsYXJhdGlvbik7XG4gICAgfSBlbHNlIGlmIChkZWNsYXJhdGlvbi50eXBlID09PSBWQVJJQUJMRV9ERUNMQVJBVElPTikge1xuICAgICAgZGVjbGFyYXRpb24uZGVjbGFyYXRpb25zLmZvckVhY2goKHsgaWQgfSkgPT4ge1xuICAgICAgICBpZiAoaWQudHlwZSA9PT0gT0JKRUNUX1BBVFRFUk4pIHtcbiAgICAgICAgICByZWN1cnNpdmVQYXR0ZXJuQ2FwdHVyZShpZCwgKHBhdHRlcm4pID0+IHtcbiAgICAgICAgICAgIGlmIChwYXR0ZXJuLnR5cGUgPT09IElERU5USUZJRVIpIHtcbiAgICAgICAgICAgICAgY2IocGF0dGVybi5uYW1lLCBmYWxzZSk7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgfSk7XG4gICAgICAgIH0gZWxzZSBpZiAoaWQudHlwZSA9PT0gQVJSQVlfUEFUVEVSTikge1xuICAgICAgICAgIGlkLmVsZW1lbnRzLmZvckVhY2goKHsgbmFtZSB9KSA9PiB7XG4gICAgICAgICAgICBjYihuYW1lLCBmYWxzZSk7XG4gICAgICAgICAgfSk7XG4gICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgY2IoaWQubmFtZSwgZmFsc2UpO1xuICAgICAgICB9XG4gICAgICB9KTtcbiAgICB9XG4gIH1cbn1cblxuLyoqXG4gKiBMaXN0IG9mIGltcG9ydHMgcGVyIGZpbGUuXG4gKlxuICogUmVwcmVzZW50ZWQgYnkgYSB0d28tbGV2ZWwgTWFwIHRvIGEgU2V0IG9mIGlkZW50aWZpZXJzLiBUaGUgdXBwZXItbGV2ZWwgTWFwXG4gKiBrZXlzIGFyZSB0aGUgcGF0aHMgdG8gdGhlIG1vZHVsZXMgY29udGFpbmluZyB0aGUgaW1wb3J0cywgd2hpbGUgdGhlXG4gKiBsb3dlci1sZXZlbCBNYXAga2V5cyBhcmUgdGhlIHBhdGhzIHRvIHRoZSBmaWxlcyB3aGljaCBhcmUgYmVpbmcgaW1wb3J0ZWRcbiAqIGZyb20uIExhc3RseSwgdGhlIFNldCBvZiBpZGVudGlmaWVycyBjb250YWlucyBlaXRoZXIgbmFtZXMgYmVpbmcgaW1wb3J0ZWRcbiAqIG9yIGEgc3BlY2lhbCBBU1Qgbm9kZSBuYW1lIGxpc3RlZCBhYm92ZSAoZS5nIEltcG9ydERlZmF1bHRTcGVjaWZpZXIpLlxuICpcbiAqIEZvciBleGFtcGxlLCBpZiB3ZSBoYXZlIGEgZmlsZSBuYW1lZCBmb28uanMgY29udGFpbmluZzpcbiAqXG4gKiAgIGltcG9ydCB7IG8yIH0gZnJvbSAnLi9iYXIuanMnO1xuICpcbiAqIFRoZW4gd2Ugd2lsbCBoYXZlIGEgc3RydWN0dXJlIHRoYXQgbG9va3MgbGlrZTpcbiAqXG4gKiAgIE1hcCB7ICdmb28uanMnID0+IE1hcCB7ICdiYXIuanMnID0+IFNldCB7ICdvMicgfSB9IH1cbiAqXG4gKiBAdHlwZSB7TWFwPHN0cmluZywgTWFwPHN0cmluZywgU2V0PHN0cmluZz4+Pn1cbiAqL1xuY29uc3QgaW1wb3J0TGlzdCA9IG5ldyBNYXAoKTtcblxuLyoqXG4gKiBMaXN0IG9mIGV4cG9ydHMgcGVyIGZpbGUuXG4gKlxuICogUmVwcmVzZW50ZWQgYnkgYSB0d28tbGV2ZWwgTWFwIHRvIGFuIG9iamVjdCBvZiBtZXRhZGF0YS4gVGhlIHVwcGVyLWxldmVsIE1hcFxuICoga2V5cyBhcmUgdGhlIHBhdGhzIHRvIHRoZSBtb2R1bGVzIGNvbnRhaW5pbmcgdGhlIGV4cG9ydHMsIHdoaWxlIHRoZVxuICogbG93ZXItbGV2ZWwgTWFwIGtleXMgYXJlIHRoZSBzcGVjaWZpYyBpZGVudGlmaWVycyBvciBzcGVjaWFsIEFTVCBub2RlIG5hbWVzXG4gKiBiZWluZyBleHBvcnRlZC4gVGhlIGxlYWYtbGV2ZWwgbWV0YWRhdGEgb2JqZWN0IGF0IHRoZSBtb21lbnQgb25seSBjb250YWlucyBhXG4gKiBgd2hlcmVVc2VkYCBwcm9wZXJ0eSwgd2hpY2ggY29udGFpbnMgYSBTZXQgb2YgcGF0aHMgdG8gbW9kdWxlcyB0aGF0IGltcG9ydFxuICogdGhlIG5hbWUuXG4gKlxuICogRm9yIGV4YW1wbGUsIGlmIHdlIGhhdmUgYSBmaWxlIG5hbWVkIGJhci5qcyBjb250YWluaW5nIHRoZSBmb2xsb3dpbmcgZXhwb3J0czpcbiAqXG4gKiAgIGNvbnN0IG8yID0gJ2Jhcic7XG4gKiAgIGV4cG9ydCB7IG8yIH07XG4gKlxuICogQW5kIGEgZmlsZSBuYW1lZCBmb28uanMgY29udGFpbmluZyB0aGUgZm9sbG93aW5nIGltcG9ydDpcbiAqXG4gKiAgIGltcG9ydCB7IG8yIH0gZnJvbSAnLi9iYXIuanMnO1xuICpcbiAqIFRoZW4gd2Ugd2lsbCBoYXZlIGEgc3RydWN0dXJlIHRoYXQgbG9va3MgbGlrZTpcbiAqXG4gKiAgIE1hcCB7ICdiYXIuanMnID0+IE1hcCB7ICdvMicgPT4geyB3aGVyZVVzZWQ6IFNldCB7ICdmb28uanMnIH0gfSB9IH1cbiAqXG4gKiBAdHlwZSB7TWFwPHN0cmluZywgTWFwPHN0cmluZywgb2JqZWN0Pj59XG4gKi9cbmNvbnN0IGV4cG9ydExpc3QgPSBuZXcgTWFwKCk7XG5cbmNvbnN0IHZpc2l0b3JLZXlNYXAgPSBuZXcgTWFwKCk7XG5cbi8qKiBAdHlwZSB7U2V0PHN0cmluZz59ICovXG5jb25zdCBpZ25vcmVkRmlsZXMgPSBuZXcgU2V0KCk7XG5jb25zdCBmaWxlc091dHNpZGVTcmMgPSBuZXcgU2V0KCk7XG5cbmNvbnN0IGlzTm9kZU1vZHVsZSA9IChwYXRoKSA9PiAoL1xcLyhub2RlX21vZHVsZXMpXFwvLykudGVzdChwYXRoKTtcblxuLyoqXG4gKiByZWFkIGFsbCBmaWxlcyBtYXRjaGluZyB0aGUgcGF0dGVybnMgaW4gc3JjIGFuZCBpZ25vcmVFeHBvcnRzXG4gKlxuICogcmV0dXJuIGFsbCBmaWxlcyBtYXRjaGluZyBzcmMgcGF0dGVybiwgd2hpY2ggYXJlIG5vdCBtYXRjaGluZyB0aGUgaWdub3JlRXhwb3J0cyBwYXR0ZXJuXG4gKiBAdHlwZSB7KHNyYzogc3RyaW5nLCBpZ25vcmVFeHBvcnRzOiBzdHJpbmcsIGNvbnRleHQ6IGltcG9ydCgnZXNsaW50JykuUnVsZS5SdWxlQ29udGV4dCkgPT4gU2V0PHN0cmluZz59XG4gKi9cbmZ1bmN0aW9uIHJlc29sdmVGaWxlcyhzcmMsIGlnbm9yZUV4cG9ydHMsIGNvbnRleHQpIHtcbiAgY29uc3QgZXh0ZW5zaW9ucyA9IEFycmF5LmZyb20oZ2V0RmlsZUV4dGVuc2lvbnMoY29udGV4dC5zZXR0aW5ncykpO1xuXG4gIGNvbnN0IHNyY0ZpbGVMaXN0ID0gbGlzdEZpbGVzVG9Qcm9jZXNzKHNyYywgZXh0ZW5zaW9ucywgY29udGV4dCk7XG5cbiAgLy8gcHJlcGFyZSBsaXN0IG9mIGlnbm9yZWQgZmlsZXNcbiAgY29uc3QgaWdub3JlZEZpbGVzTGlzdCA9IGxpc3RGaWxlc1RvUHJvY2VzcyhpZ25vcmVFeHBvcnRzLCBleHRlbnNpb25zLCBjb250ZXh0KTtcblxuICAvLyBUaGUgbW9kZXJuIGFwaSB3aWxsIHJldHVybiBhIGxpc3Qgb2YgZmlsZSBwYXRocywgcmF0aGVyIHRoYW4gYW4gb2JqZWN0XG4gIGlmIChpZ25vcmVkRmlsZXNMaXN0Lmxlbmd0aCAmJiB0eXBlb2YgaWdub3JlZEZpbGVzTGlzdFswXSA9PT0gJ3N0cmluZycpIHtcbiAgICBpZ25vcmVkRmlsZXNMaXN0LmZvckVhY2goKGZpbGVuYW1lKSA9PiBpZ25vcmVkRmlsZXMuYWRkKGZpbGVuYW1lKSk7XG4gIH0gZWxzZSB7XG4gICAgaWdub3JlZEZpbGVzTGlzdC5mb3JFYWNoKCh7IGZpbGVuYW1lIH0pID0+IGlnbm9yZWRGaWxlcy5hZGQoZmlsZW5hbWUpKTtcbiAgfVxuXG4gIC8vIHByZXBhcmUgbGlzdCBvZiBzb3VyY2UgZmlsZXMsIGRvbid0IGNvbnNpZGVyIGZpbGVzIGZyb20gbm9kZV9tb2R1bGVzXG4gIGNvbnN0IHJlc29sdmVkRmlsZXMgPSBzcmNGaWxlTGlzdC5sZW5ndGggJiYgdHlwZW9mIHNyY0ZpbGVMaXN0WzBdID09PSAnc3RyaW5nJ1xuICAgID8gc3JjRmlsZUxpc3QuZmlsdGVyKChmaWxlUGF0aCkgPT4gIWlzTm9kZU1vZHVsZShmaWxlUGF0aCkpXG4gICAgOiBmbGF0TWFwKHNyY0ZpbGVMaXN0LCAoeyBmaWxlbmFtZSB9KSA9PiBpc05vZGVNb2R1bGUoZmlsZW5hbWUpID8gW10gOiBmaWxlbmFtZSk7XG5cbiAgcmV0dXJuIG5ldyBTZXQocmVzb2x2ZWRGaWxlcyk7XG59XG5cbi8qKlxuICogcGFyc2UgYWxsIHNvdXJjZSBmaWxlcyBhbmQgYnVpbGQgdXAgMiBtYXBzIGNvbnRhaW5pbmcgdGhlIGV4aXN0aW5nIGltcG9ydHMgYW5kIGV4cG9ydHNcbiAqL1xuY29uc3QgcHJlcGFyZUltcG9ydHNBbmRFeHBvcnRzID0gKHNyY0ZpbGVzLCBjb250ZXh0KSA9PiB7XG4gIGNvbnN0IGV4cG9ydEFsbCA9IG5ldyBNYXAoKTtcbiAgc3JjRmlsZXMuZm9yRWFjaCgoZmlsZSkgPT4ge1xuICAgIGNvbnN0IGV4cG9ydHMgPSBuZXcgTWFwKCk7XG4gICAgY29uc3QgaW1wb3J0cyA9IG5ldyBNYXAoKTtcbiAgICBjb25zdCBjdXJyZW50RXhwb3J0cyA9IEV4cG9ydE1hcEJ1aWxkZXIuZ2V0KGZpbGUsIGNvbnRleHQpO1xuICAgIGlmIChjdXJyZW50RXhwb3J0cykge1xuICAgICAgY29uc3Qge1xuICAgICAgICBkZXBlbmRlbmNpZXMsXG4gICAgICAgIHJlZXhwb3J0cyxcbiAgICAgICAgaW1wb3J0czogbG9jYWxJbXBvcnRMaXN0LFxuICAgICAgICBuYW1lc3BhY2UsXG4gICAgICAgIHZpc2l0b3JLZXlzLFxuICAgICAgfSA9IGN1cnJlbnRFeHBvcnRzO1xuXG4gICAgICB2aXNpdG9yS2V5TWFwLnNldChmaWxlLCB2aXNpdG9yS2V5cyk7XG4gICAgICAvLyBkZXBlbmRlbmNpZXMgPT09IGV4cG9ydCAqIGZyb21cbiAgICAgIGNvbnN0IGN1cnJlbnRFeHBvcnRBbGwgPSBuZXcgU2V0KCk7XG4gICAgICBkZXBlbmRlbmNpZXMuZm9yRWFjaCgoZ2V0RGVwZW5kZW5jeSkgPT4ge1xuICAgICAgICBjb25zdCBkZXBlbmRlbmN5ID0gZ2V0RGVwZW5kZW5jeSgpO1xuICAgICAgICBpZiAoZGVwZW5kZW5jeSA9PT0gbnVsbCkge1xuICAgICAgICAgIHJldHVybjtcbiAgICAgICAgfVxuXG4gICAgICAgIGN1cnJlbnRFeHBvcnRBbGwuYWRkKGRlcGVuZGVuY3kucGF0aCk7XG4gICAgICB9KTtcbiAgICAgIGV4cG9ydEFsbC5zZXQoZmlsZSwgY3VycmVudEV4cG9ydEFsbCk7XG5cbiAgICAgIHJlZXhwb3J0cy5mb3JFYWNoKCh2YWx1ZSwga2V5KSA9PiB7XG4gICAgICAgIGlmIChrZXkgPT09IERFRkFVTFQpIHtcbiAgICAgICAgICBleHBvcnRzLnNldChJTVBPUlRfREVGQVVMVF9TUEVDSUZJRVIsIHsgd2hlcmVVc2VkOiBuZXcgU2V0KCkgfSk7XG4gICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgZXhwb3J0cy5zZXQoa2V5LCB7IHdoZXJlVXNlZDogbmV3IFNldCgpIH0pO1xuICAgICAgICB9XG4gICAgICAgIGNvbnN0IHJlZXhwb3J0ID0gdmFsdWUuZ2V0SW1wb3J0KCk7XG4gICAgICAgIGlmICghcmVleHBvcnQpIHtcbiAgICAgICAgICByZXR1cm47XG4gICAgICAgIH1cbiAgICAgICAgbGV0IGxvY2FsSW1wb3J0ID0gaW1wb3J0cy5nZXQocmVleHBvcnQucGF0aCk7XG4gICAgICAgIGxldCBjdXJyZW50VmFsdWU7XG4gICAgICAgIGlmICh2YWx1ZS5sb2NhbCA9PT0gREVGQVVMVCkge1xuICAgICAgICAgIGN1cnJlbnRWYWx1ZSA9IElNUE9SVF9ERUZBVUxUX1NQRUNJRklFUjtcbiAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICBjdXJyZW50VmFsdWUgPSB2YWx1ZS5sb2NhbDtcbiAgICAgICAgfVxuICAgICAgICBpZiAodHlwZW9mIGxvY2FsSW1wb3J0ICE9PSAndW5kZWZpbmVkJykge1xuICAgICAgICAgIGxvY2FsSW1wb3J0ID0gbmV3IFNldChbLi4ubG9jYWxJbXBvcnQsIGN1cnJlbnRWYWx1ZV0pO1xuICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgIGxvY2FsSW1wb3J0ID0gbmV3IFNldChbY3VycmVudFZhbHVlXSk7XG4gICAgICAgIH1cbiAgICAgICAgaW1wb3J0cy5zZXQocmVleHBvcnQucGF0aCwgbG9jYWxJbXBvcnQpO1xuICAgICAgfSk7XG5cbiAgICAgIGxvY2FsSW1wb3J0TGlzdC5mb3JFYWNoKCh2YWx1ZSwga2V5KSA9PiB7XG4gICAgICAgIGlmIChpc05vZGVNb2R1bGUoa2V5KSkge1xuICAgICAgICAgIHJldHVybjtcbiAgICAgICAgfVxuICAgICAgICBjb25zdCBsb2NhbEltcG9ydCA9IGltcG9ydHMuZ2V0KGtleSkgfHwgbmV3IFNldCgpO1xuICAgICAgICB2YWx1ZS5kZWNsYXJhdGlvbnMuZm9yRWFjaCgoeyBpbXBvcnRlZFNwZWNpZmllcnMgfSkgPT4ge1xuICAgICAgICAgIGltcG9ydGVkU3BlY2lmaWVycy5mb3JFYWNoKChzcGVjaWZpZXIpID0+IHtcbiAgICAgICAgICAgIGxvY2FsSW1wb3J0LmFkZChzcGVjaWZpZXIpO1xuICAgICAgICAgIH0pO1xuICAgICAgICB9KTtcbiAgICAgICAgaW1wb3J0cy5zZXQoa2V5LCBsb2NhbEltcG9ydCk7XG4gICAgICB9KTtcbiAgICAgIGltcG9ydExpc3Quc2V0KGZpbGUsIGltcG9ydHMpO1xuXG4gICAgICAvLyBidWlsZCB1cCBleHBvcnQgbGlzdCBvbmx5LCBpZiBmaWxlIGlzIG5vdCBpZ25vcmVkXG4gICAgICBpZiAoaWdub3JlZEZpbGVzLmhhcyhmaWxlKSkge1xuICAgICAgICByZXR1cm47XG4gICAgICB9XG4gICAgICBuYW1lc3BhY2UuZm9yRWFjaCgodmFsdWUsIGtleSkgPT4ge1xuICAgICAgICBpZiAoa2V5ID09PSBERUZBVUxUKSB7XG4gICAgICAgICAgZXhwb3J0cy5zZXQoSU1QT1JUX0RFRkFVTFRfU1BFQ0lGSUVSLCB7IHdoZXJlVXNlZDogbmV3IFNldCgpIH0pO1xuICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgIGV4cG9ydHMuc2V0KGtleSwgeyB3aGVyZVVzZWQ6IG5ldyBTZXQoKSB9KTtcbiAgICAgICAgfVxuICAgICAgfSk7XG4gICAgfVxuICAgIGV4cG9ydHMuc2V0KEVYUE9SVF9BTExfREVDTEFSQVRJT04sIHsgd2hlcmVVc2VkOiBuZXcgU2V0KCkgfSk7XG4gICAgZXhwb3J0cy5zZXQoSU1QT1JUX05BTUVTUEFDRV9TUEVDSUZJRVIsIHsgd2hlcmVVc2VkOiBuZXcgU2V0KCkgfSk7XG4gICAgZXhwb3J0TGlzdC5zZXQoZmlsZSwgZXhwb3J0cyk7XG4gIH0pO1xuICBleHBvcnRBbGwuZm9yRWFjaCgodmFsdWUsIGtleSkgPT4ge1xuICAgIHZhbHVlLmZvckVhY2goKHZhbCkgPT4ge1xuICAgICAgY29uc3QgY3VycmVudEV4cG9ydHMgPSBleHBvcnRMaXN0LmdldCh2YWwpO1xuICAgICAgaWYgKGN1cnJlbnRFeHBvcnRzKSB7XG4gICAgICAgIGNvbnN0IGN1cnJlbnRFeHBvcnQgPSBjdXJyZW50RXhwb3J0cy5nZXQoRVhQT1JUX0FMTF9ERUNMQVJBVElPTik7XG4gICAgICAgIGN1cnJlbnRFeHBvcnQud2hlcmVVc2VkLmFkZChrZXkpO1xuICAgICAgfVxuICAgIH0pO1xuICB9KTtcbn07XG5cbi8qKlxuICogdHJhdmVyc2UgdGhyb3VnaCBhbGwgaW1wb3J0cyBhbmQgYWRkIHRoZSByZXNwZWN0aXZlIHBhdGggdG8gdGhlIHdoZXJlVXNlZC1saXN0XG4gKiBvZiB0aGUgY29ycmVzcG9uZGluZyBleHBvcnRcbiAqL1xuY29uc3QgZGV0ZXJtaW5lVXNhZ2UgPSAoKSA9PiB7XG4gIGltcG9ydExpc3QuZm9yRWFjaCgobGlzdFZhbHVlLCBsaXN0S2V5KSA9PiB7XG4gICAgbGlzdFZhbHVlLmZvckVhY2goKHZhbHVlLCBrZXkpID0+IHtcbiAgICAgIGNvbnN0IGV4cG9ydHMgPSBleHBvcnRMaXN0LmdldChrZXkpO1xuICAgICAgaWYgKHR5cGVvZiBleHBvcnRzICE9PSAndW5kZWZpbmVkJykge1xuICAgICAgICB2YWx1ZS5mb3JFYWNoKChjdXJyZW50SW1wb3J0KSA9PiB7XG4gICAgICAgICAgbGV0IHNwZWNpZmllcjtcbiAgICAgICAgICBpZiAoY3VycmVudEltcG9ydCA9PT0gSU1QT1JUX05BTUVTUEFDRV9TUEVDSUZJRVIpIHtcbiAgICAgICAgICAgIHNwZWNpZmllciA9IElNUE9SVF9OQU1FU1BBQ0VfU1BFQ0lGSUVSO1xuICAgICAgICAgIH0gZWxzZSBpZiAoY3VycmVudEltcG9ydCA9PT0gSU1QT1JUX0RFRkFVTFRfU1BFQ0lGSUVSKSB7XG4gICAgICAgICAgICBzcGVjaWZpZXIgPSBJTVBPUlRfREVGQVVMVF9TUEVDSUZJRVI7XG4gICAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICAgIHNwZWNpZmllciA9IGN1cnJlbnRJbXBvcnQ7XG4gICAgICAgICAgfVxuICAgICAgICAgIGlmICh0eXBlb2Ygc3BlY2lmaWVyICE9PSAndW5kZWZpbmVkJykge1xuICAgICAgICAgICAgY29uc3QgZXhwb3J0U3RhdGVtZW50ID0gZXhwb3J0cy5nZXQoc3BlY2lmaWVyKTtcbiAgICAgICAgICAgIGlmICh0eXBlb2YgZXhwb3J0U3RhdGVtZW50ICE9PSAndW5kZWZpbmVkJykge1xuICAgICAgICAgICAgICBjb25zdCB7IHdoZXJlVXNlZCB9ID0gZXhwb3J0U3RhdGVtZW50O1xuICAgICAgICAgICAgICB3aGVyZVVzZWQuYWRkKGxpc3RLZXkpO1xuICAgICAgICAgICAgICBleHBvcnRzLnNldChzcGVjaWZpZXIsIHsgd2hlcmVVc2VkIH0pO1xuICAgICAgICAgICAgfVxuICAgICAgICAgIH1cbiAgICAgICAgfSk7XG4gICAgICB9XG4gICAgfSk7XG4gIH0pO1xufTtcblxuY29uc3QgZ2V0U3JjID0gKHNyYykgPT4ge1xuICBpZiAoc3JjKSB7XG4gICAgcmV0dXJuIHNyYztcbiAgfVxuICByZXR1cm4gW3Byb2Nlc3MuY3dkKCldO1xufTtcblxuLyoqXG4gKiBwcmVwYXJlIHRoZSBsaXN0cyBvZiBleGlzdGluZyBpbXBvcnRzIGFuZCBleHBvcnRzIC0gc2hvdWxkIG9ubHkgYmUgZXhlY3V0ZWQgb25jZSBhdFxuICogdGhlIHN0YXJ0IG9mIGEgbmV3IGVzbGludCBydW5cbiAqL1xuLyoqIEB0eXBlIHtTZXQ8c3RyaW5nPn0gKi9cbmxldCBzcmNGaWxlcztcbmxldCBsYXN0UHJlcGFyZUtleTtcbmNvbnN0IGRvUHJlcGFyYXRpb24gPSAoc3JjLCBpZ25vcmVFeHBvcnRzLCBjb250ZXh0KSA9PiB7XG4gIGNvbnN0IHByZXBhcmVLZXkgPSBKU09OLnN0cmluZ2lmeSh7XG4gICAgc3JjOiAoc3JjIHx8IFtdKS5zb3J0KCksXG4gICAgaWdub3JlRXhwb3J0czogKGlnbm9yZUV4cG9ydHMgfHwgW10pLnNvcnQoKSxcbiAgICBleHRlbnNpb25zOiBBcnJheS5mcm9tKGdldEZpbGVFeHRlbnNpb25zKGNvbnRleHQuc2V0dGluZ3MpKS5zb3J0KCksXG4gIH0pO1xuICBpZiAocHJlcGFyZUtleSA9PT0gbGFzdFByZXBhcmVLZXkpIHtcbiAgICByZXR1cm47XG4gIH1cblxuICBpbXBvcnRMaXN0LmNsZWFyKCk7XG4gIGV4cG9ydExpc3QuY2xlYXIoKTtcbiAgaWdub3JlZEZpbGVzLmNsZWFyKCk7XG4gIGZpbGVzT3V0c2lkZVNyYy5jbGVhcigpO1xuXG4gIHNyY0ZpbGVzID0gcmVzb2x2ZUZpbGVzKGdldFNyYyhzcmMpLCBpZ25vcmVFeHBvcnRzLCBjb250ZXh0KTtcbiAgcHJlcGFyZUltcG9ydHNBbmRFeHBvcnRzKHNyY0ZpbGVzLCBjb250ZXh0KTtcbiAgZGV0ZXJtaW5lVXNhZ2UoKTtcbiAgbGFzdFByZXBhcmVLZXkgPSBwcmVwYXJlS2V5O1xufTtcblxuY29uc3QgbmV3TmFtZXNwYWNlSW1wb3J0RXhpc3RzID0gKHNwZWNpZmllcnMpID0+IHNwZWNpZmllcnMuc29tZSgoeyB0eXBlIH0pID0+IHR5cGUgPT09IElNUE9SVF9OQU1FU1BBQ0VfU1BFQ0lGSUVSKTtcblxuY29uc3QgbmV3RGVmYXVsdEltcG9ydEV4aXN0cyA9IChzcGVjaWZpZXJzKSA9PiBzcGVjaWZpZXJzLnNvbWUoKHsgdHlwZSB9KSA9PiB0eXBlID09PSBJTVBPUlRfREVGQVVMVF9TUEVDSUZJRVIpO1xuXG5jb25zdCBmaWxlSXNJblBrZyA9IChmaWxlKSA9PiB7XG4gIGNvbnN0IHsgcGF0aCwgcGtnIH0gPSByZWFkUGtnVXAoeyBjd2Q6IGZpbGUgfSk7XG4gIGNvbnN0IGJhc2VQYXRoID0gZGlybmFtZShwYXRoKTtcblxuICBjb25zdCBjaGVja1BrZ0ZpZWxkU3RyaW5nID0gKHBrZ0ZpZWxkKSA9PiB7XG4gICAgaWYgKGpvaW4oYmFzZVBhdGgsIHBrZ0ZpZWxkKSA9PT0gZmlsZSkge1xuICAgICAgcmV0dXJuIHRydWU7XG4gICAgfVxuICB9O1xuXG4gIGNvbnN0IGNoZWNrUGtnRmllbGRPYmplY3QgPSAocGtnRmllbGQpID0+IHtcbiAgICBjb25zdCBwa2dGaWVsZEZpbGVzID0gZmxhdE1hcCh2YWx1ZXMocGtnRmllbGQpLCAodmFsdWUpID0+IHR5cGVvZiB2YWx1ZSA9PT0gJ2Jvb2xlYW4nID8gW10gOiBqb2luKGJhc2VQYXRoLCB2YWx1ZSkpO1xuXG4gICAgaWYgKGluY2x1ZGVzKHBrZ0ZpZWxkRmlsZXMsIGZpbGUpKSB7XG4gICAgICByZXR1cm4gdHJ1ZTtcbiAgICB9XG4gIH07XG5cbiAgY29uc3QgY2hlY2tQa2dGaWVsZCA9IChwa2dGaWVsZCkgPT4ge1xuICAgIGlmICh0eXBlb2YgcGtnRmllbGQgPT09ICdzdHJpbmcnKSB7XG4gICAgICByZXR1cm4gY2hlY2tQa2dGaWVsZFN0cmluZyhwa2dGaWVsZCk7XG4gICAgfVxuXG4gICAgaWYgKHR5cGVvZiBwa2dGaWVsZCA9PT0gJ29iamVjdCcpIHtcbiAgICAgIHJldHVybiBjaGVja1BrZ0ZpZWxkT2JqZWN0KHBrZ0ZpZWxkKTtcbiAgICB9XG4gIH07XG5cbiAgaWYgKHBrZy5wcml2YXRlID09PSB0cnVlKSB7XG4gICAgcmV0dXJuIGZhbHNlO1xuICB9XG5cbiAgaWYgKHBrZy5iaW4pIHtcbiAgICBpZiAoY2hlY2tQa2dGaWVsZChwa2cuYmluKSkge1xuICAgICAgcmV0dXJuIHRydWU7XG4gICAgfVxuICB9XG5cbiAgaWYgKHBrZy5icm93c2VyKSB7XG4gICAgaWYgKGNoZWNrUGtnRmllbGQocGtnLmJyb3dzZXIpKSB7XG4gICAgICByZXR1cm4gdHJ1ZTtcbiAgICB9XG4gIH1cblxuICBpZiAocGtnLm1haW4pIHtcbiAgICBpZiAoY2hlY2tQa2dGaWVsZFN0cmluZyhwa2cubWFpbikpIHtcbiAgICAgIHJldHVybiB0cnVlO1xuICAgIH1cbiAgfVxuXG4gIHJldHVybiBmYWxzZTtcbn07XG5cbm1vZHVsZS5leHBvcnRzID0ge1xuICBtZXRhOiB7XG4gICAgdHlwZTogJ3N1Z2dlc3Rpb24nLFxuICAgIGRvY3M6IHtcbiAgICAgIGNhdGVnb3J5OiAnSGVscGZ1bCB3YXJuaW5ncycsXG4gICAgICBkZXNjcmlwdGlvbjogJ0ZvcmJpZCBtb2R1bGVzIHdpdGhvdXQgZXhwb3J0cywgb3IgZXhwb3J0cyB3aXRob3V0IG1hdGNoaW5nIGltcG9ydCBpbiBhbm90aGVyIG1vZHVsZS4nLFxuICAgICAgdXJsOiBkb2NzVXJsKCduby11bnVzZWQtbW9kdWxlcycpLFxuICAgIH0sXG4gICAgc2NoZW1hOiBbe1xuICAgICAgcHJvcGVydGllczoge1xuICAgICAgICBzcmM6IHtcbiAgICAgICAgICBkZXNjcmlwdGlvbjogJ2ZpbGVzL3BhdGhzIHRvIGJlIGFuYWx5emVkIChvbmx5IGZvciB1bnVzZWQgZXhwb3J0cyknLFxuICAgICAgICAgIHR5cGU6ICdhcnJheScsXG4gICAgICAgICAgdW5pcXVlSXRlbXM6IHRydWUsXG4gICAgICAgICAgaXRlbXM6IHtcbiAgICAgICAgICAgIHR5cGU6ICdzdHJpbmcnLFxuICAgICAgICAgICAgbWluTGVuZ3RoOiAxLFxuICAgICAgICAgIH0sXG4gICAgICAgIH0sXG4gICAgICAgIGlnbm9yZUV4cG9ydHM6IHtcbiAgICAgICAgICBkZXNjcmlwdGlvbjogJ2ZpbGVzL3BhdGhzIGZvciB3aGljaCB1bnVzZWQgZXhwb3J0cyB3aWxsIG5vdCBiZSByZXBvcnRlZCAoZS5nIG1vZHVsZSBlbnRyeSBwb2ludHMpJyxcbiAgICAgICAgICB0eXBlOiAnYXJyYXknLFxuICAgICAgICAgIHVuaXF1ZUl0ZW1zOiB0cnVlLFxuICAgICAgICAgIGl0ZW1zOiB7XG4gICAgICAgICAgICB0eXBlOiAnc3RyaW5nJyxcbiAgICAgICAgICAgIG1pbkxlbmd0aDogMSxcbiAgICAgICAgICB9LFxuICAgICAgICB9LFxuICAgICAgICBtaXNzaW5nRXhwb3J0czoge1xuICAgICAgICAgIGRlc2NyaXB0aW9uOiAncmVwb3J0IG1vZHVsZXMgd2l0aG91dCBhbnkgZXhwb3J0cycsXG4gICAgICAgICAgdHlwZTogJ2Jvb2xlYW4nLFxuICAgICAgICB9LFxuICAgICAgICB1bnVzZWRFeHBvcnRzOiB7XG4gICAgICAgICAgZGVzY3JpcHRpb246ICdyZXBvcnQgZXhwb3J0cyB3aXRob3V0IGFueSB1c2FnZScsXG4gICAgICAgICAgdHlwZTogJ2Jvb2xlYW4nLFxuICAgICAgICB9LFxuICAgICAgICBpZ25vcmVVbnVzZWRUeXBlRXhwb3J0czoge1xuICAgICAgICAgIGRlc2NyaXB0aW9uOiAnaWdub3JlIHR5cGUgZXhwb3J0cyB3aXRob3V0IGFueSB1c2FnZScsXG4gICAgICAgICAgdHlwZTogJ2Jvb2xlYW4nLFxuICAgICAgICB9LFxuICAgICAgfSxcbiAgICAgIGFueU9mOiBbXG4gICAgICAgIHtcbiAgICAgICAgICBwcm9wZXJ0aWVzOiB7XG4gICAgICAgICAgICB1bnVzZWRFeHBvcnRzOiB7IGVudW06IFt0cnVlXSB9LFxuICAgICAgICAgICAgc3JjOiB7XG4gICAgICAgICAgICAgIG1pbkl0ZW1zOiAxLFxuICAgICAgICAgICAgfSxcbiAgICAgICAgICB9LFxuICAgICAgICAgIHJlcXVpcmVkOiBbJ3VudXNlZEV4cG9ydHMnXSxcbiAgICAgICAgfSxcbiAgICAgICAge1xuICAgICAgICAgIHByb3BlcnRpZXM6IHtcbiAgICAgICAgICAgIG1pc3NpbmdFeHBvcnRzOiB7IGVudW06IFt0cnVlXSB9LFxuICAgICAgICAgIH0sXG4gICAgICAgICAgcmVxdWlyZWQ6IFsnbWlzc2luZ0V4cG9ydHMnXSxcbiAgICAgICAgfSxcbiAgICAgIF0sXG4gICAgfV0sXG4gIH0sXG5cbiAgY3JlYXRlKGNvbnRleHQpIHtcbiAgICBjb25zdCB7XG4gICAgICBzcmMsXG4gICAgICBpZ25vcmVFeHBvcnRzID0gW10sXG4gICAgICBtaXNzaW5nRXhwb3J0cyxcbiAgICAgIHVudXNlZEV4cG9ydHMsXG4gICAgICBpZ25vcmVVbnVzZWRUeXBlRXhwb3J0cyxcbiAgICB9ID0gY29udGV4dC5vcHRpb25zWzBdIHx8IHt9O1xuXG4gICAgaWYgKHVudXNlZEV4cG9ydHMpIHtcbiAgICAgIGRvUHJlcGFyYXRpb24oc3JjLCBpZ25vcmVFeHBvcnRzLCBjb250ZXh0KTtcbiAgICB9XG5cbiAgICBjb25zdCBmaWxlID0gZ2V0UGh5c2ljYWxGaWxlbmFtZShjb250ZXh0KTtcblxuICAgIGNvbnN0IGNoZWNrRXhwb3J0UHJlc2VuY2UgPSAobm9kZSkgPT4ge1xuICAgICAgaWYgKCFtaXNzaW5nRXhwb3J0cykge1xuICAgICAgICByZXR1cm47XG4gICAgICB9XG5cbiAgICAgIGlmIChpZ25vcmVkRmlsZXMuaGFzKGZpbGUpKSB7XG4gICAgICAgIHJldHVybjtcbiAgICAgIH1cblxuICAgICAgY29uc3QgZXhwb3J0Q291bnQgPSBleHBvcnRMaXN0LmdldChmaWxlKTtcbiAgICAgIGNvbnN0IGV4cG9ydEFsbCA9IGV4cG9ydENvdW50LmdldChFWFBPUlRfQUxMX0RFQ0xBUkFUSU9OKTtcbiAgICAgIGNvbnN0IG5hbWVzcGFjZUltcG9ydHMgPSBleHBvcnRDb3VudC5nZXQoSU1QT1JUX05BTUVTUEFDRV9TUEVDSUZJRVIpO1xuXG4gICAgICBleHBvcnRDb3VudC5kZWxldGUoRVhQT1JUX0FMTF9ERUNMQVJBVElPTik7XG4gICAgICBleHBvcnRDb3VudC5kZWxldGUoSU1QT1JUX05BTUVTUEFDRV9TUEVDSUZJRVIpO1xuICAgICAgaWYgKGV4cG9ydENvdW50LnNpemUgPCAxKSB7XG4gICAgICAgIC8vIG5vZGUuYm9keVswXSA9PT0gJ3VuZGVmaW5lZCcgb25seSBoYXBwZW5zLCBpZiBldmVyeXRoaW5nIGlzIGNvbW1lbnRlZCBvdXQgaW4gdGhlIGZpbGVcbiAgICAgICAgLy8gYmVpbmcgbGludGVkXG4gICAgICAgIGNvbnRleHQucmVwb3J0KG5vZGUuYm9keVswXSA/IG5vZGUuYm9keVswXSA6IG5vZGUsICdObyBleHBvcnRzIGZvdW5kJyk7XG4gICAgICB9XG4gICAgICBleHBvcnRDb3VudC5zZXQoRVhQT1JUX0FMTF9ERUNMQVJBVElPTiwgZXhwb3J0QWxsKTtcbiAgICAgIGV4cG9ydENvdW50LnNldChJTVBPUlRfTkFNRVNQQUNFX1NQRUNJRklFUiwgbmFtZXNwYWNlSW1wb3J0cyk7XG4gICAgfTtcblxuICAgIGNvbnN0IGNoZWNrVXNhZ2UgPSAobm9kZSwgZXhwb3J0ZWRWYWx1ZSwgaXNUeXBlRXhwb3J0KSA9PiB7XG4gICAgICBpZiAoIXVudXNlZEV4cG9ydHMpIHtcbiAgICAgICAgcmV0dXJuO1xuICAgICAgfVxuXG4gICAgICBpZiAoaXNUeXBlRXhwb3J0ICYmIGlnbm9yZVVudXNlZFR5cGVFeHBvcnRzKSB7XG4gICAgICAgIHJldHVybjtcbiAgICAgIH1cblxuICAgICAgaWYgKGlnbm9yZWRGaWxlcy5oYXMoZmlsZSkpIHtcbiAgICAgICAgcmV0dXJuO1xuICAgICAgfVxuXG4gICAgICBpZiAoZmlsZUlzSW5Qa2coZmlsZSkpIHtcbiAgICAgICAgcmV0dXJuO1xuICAgICAgfVxuXG4gICAgICBpZiAoZmlsZXNPdXRzaWRlU3JjLmhhcyhmaWxlKSkge1xuICAgICAgICByZXR1cm47XG4gICAgICB9XG5cbiAgICAgIC8vIG1ha2Ugc3VyZSBmaWxlIHRvIGJlIGxpbnRlZCBpcyBpbmNsdWRlZCBpbiBzb3VyY2UgZmlsZXNcbiAgICAgIGlmICghc3JjRmlsZXMuaGFzKGZpbGUpKSB7XG4gICAgICAgIHNyY0ZpbGVzID0gcmVzb2x2ZUZpbGVzKGdldFNyYyhzcmMpLCBpZ25vcmVFeHBvcnRzLCBjb250ZXh0KTtcbiAgICAgICAgaWYgKCFzcmNGaWxlcy5oYXMoZmlsZSkpIHtcbiAgICAgICAgICBmaWxlc091dHNpZGVTcmMuYWRkKGZpbGUpO1xuICAgICAgICAgIHJldHVybjtcbiAgICAgICAgfVxuICAgICAgfVxuXG4gICAgICBleHBvcnRzID0gZXhwb3J0TGlzdC5nZXQoZmlsZSk7XG5cbiAgICAgIGlmICghZXhwb3J0cykge1xuICAgICAgICBjb25zb2xlLmVycm9yKGBmaWxlIFxcYCR7ZmlsZX1cXGAgaGFzIG5vIGV4cG9ydHMuIFBsZWFzZSB1cGRhdGUgdG8gdGhlIGxhdGVzdCwgYW5kIGlmIGl0IHN0aWxsIGhhcHBlbnMsIHJlcG9ydCB0aGlzIG9uIGh0dHBzOi8vZ2l0aHViLmNvbS9pbXBvcnQtanMvZXNsaW50LXBsdWdpbi1pbXBvcnQvaXNzdWVzLzI4NjYhYCk7XG4gICAgICB9XG5cbiAgICAgIC8vIHNwZWNpYWwgY2FzZTogZXhwb3J0ICogZnJvbVxuICAgICAgY29uc3QgZXhwb3J0QWxsID0gZXhwb3J0cy5nZXQoRVhQT1JUX0FMTF9ERUNMQVJBVElPTik7XG4gICAgICBpZiAodHlwZW9mIGV4cG9ydEFsbCAhPT0gJ3VuZGVmaW5lZCcgJiYgZXhwb3J0ZWRWYWx1ZSAhPT0gSU1QT1JUX0RFRkFVTFRfU1BFQ0lGSUVSKSB7XG4gICAgICAgIGlmIChleHBvcnRBbGwud2hlcmVVc2VkLnNpemUgPiAwKSB7XG4gICAgICAgICAgcmV0dXJuO1xuICAgICAgICB9XG4gICAgICB9XG5cbiAgICAgIC8vIHNwZWNpYWwgY2FzZTogbmFtZXNwYWNlIGltcG9ydFxuICAgICAgY29uc3QgbmFtZXNwYWNlSW1wb3J0cyA9IGV4cG9ydHMuZ2V0KElNUE9SVF9OQU1FU1BBQ0VfU1BFQ0lGSUVSKTtcbiAgICAgIGlmICh0eXBlb2YgbmFtZXNwYWNlSW1wb3J0cyAhPT0gJ3VuZGVmaW5lZCcpIHtcbiAgICAgICAgaWYgKG5hbWVzcGFjZUltcG9ydHMud2hlcmVVc2VkLnNpemUgPiAwKSB7XG4gICAgICAgICAgcmV0dXJuO1xuICAgICAgICB9XG4gICAgICB9XG5cbiAgICAgIC8vIGV4cG9ydHNMaXN0IHdpbGwgYWx3YXlzIG1hcCBhbnkgaW1wb3J0ZWQgdmFsdWUgb2YgJ2RlZmF1bHQnIHRvICdJbXBvcnREZWZhdWx0U3BlY2lmaWVyJ1xuICAgICAgY29uc3QgZXhwb3J0c0tleSA9IGV4cG9ydGVkVmFsdWUgPT09IERFRkFVTFQgPyBJTVBPUlRfREVGQVVMVF9TUEVDSUZJRVIgOiBleHBvcnRlZFZhbHVlO1xuXG4gICAgICBjb25zdCBleHBvcnRTdGF0ZW1lbnQgPSBleHBvcnRzLmdldChleHBvcnRzS2V5KTtcblxuICAgICAgY29uc3QgdmFsdWUgPSBleHBvcnRzS2V5ID09PSBJTVBPUlRfREVGQVVMVF9TUEVDSUZJRVIgPyBERUZBVUxUIDogZXhwb3J0c0tleTtcblxuICAgICAgaWYgKHR5cGVvZiBleHBvcnRTdGF0ZW1lbnQgIT09ICd1bmRlZmluZWQnKSB7XG4gICAgICAgIGlmIChleHBvcnRTdGF0ZW1lbnQud2hlcmVVc2VkLnNpemUgPCAxKSB7XG4gICAgICAgICAgY29udGV4dC5yZXBvcnQoXG4gICAgICAgICAgICBub2RlLFxuICAgICAgICAgICAgYGV4cG9ydGVkIGRlY2xhcmF0aW9uICcke3ZhbHVlfScgbm90IHVzZWQgd2l0aGluIG90aGVyIG1vZHVsZXNgLFxuICAgICAgICAgICk7XG4gICAgICAgIH1cbiAgICAgIH0gZWxzZSB7XG4gICAgICAgIGNvbnRleHQucmVwb3J0KFxuICAgICAgICAgIG5vZGUsXG4gICAgICAgICAgYGV4cG9ydGVkIGRlY2xhcmF0aW9uICcke3ZhbHVlfScgbm90IHVzZWQgd2l0aGluIG90aGVyIG1vZHVsZXNgLFxuICAgICAgICApO1xuICAgICAgfVxuICAgIH07XG5cbiAgICAvKipcbiAgICAgKiBvbmx5IHVzZWZ1bCBmb3IgdG9vbHMgbGlrZSB2c2NvZGUtZXNsaW50XG4gICAgICpcbiAgICAgKiB1cGRhdGUgbGlzdHMgb2YgZXhpc3RpbmcgZXhwb3J0cyBkdXJpbmcgcnVudGltZVxuICAgICAqL1xuICAgIGNvbnN0IHVwZGF0ZUV4cG9ydFVzYWdlID0gKG5vZGUpID0+IHtcbiAgICAgIGlmIChpZ25vcmVkRmlsZXMuaGFzKGZpbGUpKSB7XG4gICAgICAgIHJldHVybjtcbiAgICAgIH1cblxuICAgICAgbGV0IGV4cG9ydHMgPSBleHBvcnRMaXN0LmdldChmaWxlKTtcblxuICAgICAgLy8gbmV3IG1vZHVsZSBoYXMgYmVlbiBjcmVhdGVkIGR1cmluZyBydW50aW1lXG4gICAgICAvLyBpbmNsdWRlIGl0IGluIGZ1cnRoZXIgcHJvY2Vzc2luZ1xuICAgICAgaWYgKHR5cGVvZiBleHBvcnRzID09PSAndW5kZWZpbmVkJykge1xuICAgICAgICBleHBvcnRzID0gbmV3IE1hcCgpO1xuICAgICAgfVxuXG4gICAgICBjb25zdCBuZXdFeHBvcnRzID0gbmV3IE1hcCgpO1xuICAgICAgY29uc3QgbmV3RXhwb3J0SWRlbnRpZmllcnMgPSBuZXcgU2V0KCk7XG5cbiAgICAgIG5vZGUuYm9keS5mb3JFYWNoKCh7IHR5cGUsIGRlY2xhcmF0aW9uLCBzcGVjaWZpZXJzIH0pID0+IHtcbiAgICAgICAgaWYgKHR5cGUgPT09IEVYUE9SVF9ERUZBVUxUX0RFQ0xBUkFUSU9OKSB7XG4gICAgICAgICAgbmV3RXhwb3J0SWRlbnRpZmllcnMuYWRkKElNUE9SVF9ERUZBVUxUX1NQRUNJRklFUik7XG4gICAgICAgIH1cbiAgICAgICAgaWYgKHR5cGUgPT09IEVYUE9SVF9OQU1FRF9ERUNMQVJBVElPTikge1xuICAgICAgICAgIGlmIChzcGVjaWZpZXJzLmxlbmd0aCA+IDApIHtcbiAgICAgICAgICAgIHNwZWNpZmllcnMuZm9yRWFjaCgoc3BlY2lmaWVyKSA9PiB7XG4gICAgICAgICAgICAgIGlmIChzcGVjaWZpZXIuZXhwb3J0ZWQpIHtcbiAgICAgICAgICAgICAgICBuZXdFeHBvcnRJZGVudGlmaWVycy5hZGQoc3BlY2lmaWVyLmV4cG9ydGVkLm5hbWUgfHwgc3BlY2lmaWVyLmV4cG9ydGVkLnZhbHVlKTtcbiAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgfSk7XG4gICAgICAgICAgfVxuICAgICAgICAgIGZvckVhY2hEZWNsYXJhdGlvbklkZW50aWZpZXIoZGVjbGFyYXRpb24sIChuYW1lKSA9PiB7XG4gICAgICAgICAgICBuZXdFeHBvcnRJZGVudGlmaWVycy5hZGQobmFtZSk7XG4gICAgICAgICAgfSk7XG4gICAgICAgIH1cbiAgICAgIH0pO1xuXG4gICAgICAvLyBvbGQgZXhwb3J0cyBleGlzdCB3aXRoaW4gbGlzdCBvZiBuZXcgZXhwb3J0cyBpZGVudGlmaWVyczogYWRkIHRvIG1hcCBvZiBuZXcgZXhwb3J0c1xuICAgICAgZXhwb3J0cy5mb3JFYWNoKCh2YWx1ZSwga2V5KSA9PiB7XG4gICAgICAgIGlmIChuZXdFeHBvcnRJZGVudGlmaWVycy5oYXMoa2V5KSkge1xuICAgICAgICAgIG5ld0V4cG9ydHMuc2V0KGtleSwgdmFsdWUpO1xuICAgICAgICB9XG4gICAgICB9KTtcblxuICAgICAgLy8gbmV3IGV4cG9ydCBpZGVudGlmaWVycyBhZGRlZDogYWRkIHRvIG1hcCBvZiBuZXcgZXhwb3J0c1xuICAgICAgbmV3RXhwb3J0SWRlbnRpZmllcnMuZm9yRWFjaCgoa2V5KSA9PiB7XG4gICAgICAgIGlmICghZXhwb3J0cy5oYXMoa2V5KSkge1xuICAgICAgICAgIG5ld0V4cG9ydHMuc2V0KGtleSwgeyB3aGVyZVVzZWQ6IG5ldyBTZXQoKSB9KTtcbiAgICAgICAgfVxuICAgICAgfSk7XG5cbiAgICAgIC8vIHByZXNlcnZlIGluZm9ybWF0aW9uIGFib3V0IG5hbWVzcGFjZSBpbXBvcnRzXG4gICAgICBjb25zdCBleHBvcnRBbGwgPSBleHBvcnRzLmdldChFWFBPUlRfQUxMX0RFQ0xBUkFUSU9OKTtcbiAgICAgIGxldCBuYW1lc3BhY2VJbXBvcnRzID0gZXhwb3J0cy5nZXQoSU1QT1JUX05BTUVTUEFDRV9TUEVDSUZJRVIpO1xuXG4gICAgICBpZiAodHlwZW9mIG5hbWVzcGFjZUltcG9ydHMgPT09ICd1bmRlZmluZWQnKSB7XG4gICAgICAgIG5hbWVzcGFjZUltcG9ydHMgPSB7IHdoZXJlVXNlZDogbmV3IFNldCgpIH07XG4gICAgICB9XG5cbiAgICAgIG5ld0V4cG9ydHMuc2V0KEVYUE9SVF9BTExfREVDTEFSQVRJT04sIGV4cG9ydEFsbCk7XG4gICAgICBuZXdFeHBvcnRzLnNldChJTVBPUlRfTkFNRVNQQUNFX1NQRUNJRklFUiwgbmFtZXNwYWNlSW1wb3J0cyk7XG4gICAgICBleHBvcnRMaXN0LnNldChmaWxlLCBuZXdFeHBvcnRzKTtcbiAgICB9O1xuXG4gICAgLyoqXG4gICAgICogb25seSB1c2VmdWwgZm9yIHRvb2xzIGxpa2UgdnNjb2RlLWVzbGludFxuICAgICAqXG4gICAgICogdXBkYXRlIGxpc3RzIG9mIGV4aXN0aW5nIGltcG9ydHMgZHVyaW5nIHJ1bnRpbWVcbiAgICAgKi9cbiAgICBjb25zdCB1cGRhdGVJbXBvcnRVc2FnZSA9IChub2RlKSA9PiB7XG4gICAgICBpZiAoIXVudXNlZEV4cG9ydHMpIHtcbiAgICAgICAgcmV0dXJuO1xuICAgICAgfVxuXG4gICAgICBsZXQgb2xkSW1wb3J0UGF0aHMgPSBpbXBvcnRMaXN0LmdldChmaWxlKTtcbiAgICAgIGlmICh0eXBlb2Ygb2xkSW1wb3J0UGF0aHMgPT09ICd1bmRlZmluZWQnKSB7XG4gICAgICAgIG9sZEltcG9ydFBhdGhzID0gbmV3IE1hcCgpO1xuICAgICAgfVxuXG4gICAgICBjb25zdCBvbGROYW1lc3BhY2VJbXBvcnRzID0gbmV3IFNldCgpO1xuICAgICAgY29uc3QgbmV3TmFtZXNwYWNlSW1wb3J0cyA9IG5ldyBTZXQoKTtcblxuICAgICAgY29uc3Qgb2xkRXhwb3J0QWxsID0gbmV3IFNldCgpO1xuICAgICAgY29uc3QgbmV3RXhwb3J0QWxsID0gbmV3IFNldCgpO1xuXG4gICAgICBjb25zdCBvbGREZWZhdWx0SW1wb3J0cyA9IG5ldyBTZXQoKTtcbiAgICAgIGNvbnN0IG5ld0RlZmF1bHRJbXBvcnRzID0gbmV3IFNldCgpO1xuXG4gICAgICBjb25zdCBvbGRJbXBvcnRzID0gbmV3IE1hcCgpO1xuICAgICAgY29uc3QgbmV3SW1wb3J0cyA9IG5ldyBNYXAoKTtcbiAgICAgIG9sZEltcG9ydFBhdGhzLmZvckVhY2goKHZhbHVlLCBrZXkpID0+IHtcbiAgICAgICAgaWYgKHZhbHVlLmhhcyhFWFBPUlRfQUxMX0RFQ0xBUkFUSU9OKSkge1xuICAgICAgICAgIG9sZEV4cG9ydEFsbC5hZGQoa2V5KTtcbiAgICAgICAgfVxuICAgICAgICBpZiAodmFsdWUuaGFzKElNUE9SVF9OQU1FU1BBQ0VfU1BFQ0lGSUVSKSkge1xuICAgICAgICAgIG9sZE5hbWVzcGFjZUltcG9ydHMuYWRkKGtleSk7XG4gICAgICAgIH1cbiAgICAgICAgaWYgKHZhbHVlLmhhcyhJTVBPUlRfREVGQVVMVF9TUEVDSUZJRVIpKSB7XG4gICAgICAgICAgb2xkRGVmYXVsdEltcG9ydHMuYWRkKGtleSk7XG4gICAgICAgIH1cbiAgICAgICAgdmFsdWUuZm9yRWFjaCgodmFsKSA9PiB7XG4gICAgICAgICAgaWYgKFxuICAgICAgICAgICAgdmFsICE9PSBJTVBPUlRfTkFNRVNQQUNFX1NQRUNJRklFUlxuICAgICAgICAgICAgJiYgdmFsICE9PSBJTVBPUlRfREVGQVVMVF9TUEVDSUZJRVJcbiAgICAgICAgICApIHtcbiAgICAgICAgICAgIG9sZEltcG9ydHMuc2V0KHZhbCwga2V5KTtcbiAgICAgICAgICB9XG4gICAgICAgIH0pO1xuICAgICAgfSk7XG5cbiAgICAgIGZ1bmN0aW9uIHByb2Nlc3NEeW5hbWljSW1wb3J0KHNvdXJjZSkge1xuICAgICAgICBpZiAoc291cmNlLnR5cGUgIT09ICdMaXRlcmFsJykge1xuICAgICAgICAgIHJldHVybiBudWxsO1xuICAgICAgICB9XG4gICAgICAgIGNvbnN0IHAgPSByZXNvbHZlKHNvdXJjZS52YWx1ZSwgY29udGV4dCk7XG4gICAgICAgIGlmIChwID09IG51bGwpIHtcbiAgICAgICAgICByZXR1cm4gbnVsbDtcbiAgICAgICAgfVxuICAgICAgICBuZXdOYW1lc3BhY2VJbXBvcnRzLmFkZChwKTtcbiAgICAgIH1cblxuICAgICAgdmlzaXQobm9kZSwgdmlzaXRvcktleU1hcC5nZXQoZmlsZSksIHtcbiAgICAgICAgSW1wb3J0RXhwcmVzc2lvbihjaGlsZCkge1xuICAgICAgICAgIHByb2Nlc3NEeW5hbWljSW1wb3J0KGNoaWxkLnNvdXJjZSk7XG4gICAgICAgIH0sXG4gICAgICAgIENhbGxFeHByZXNzaW9uKGNoaWxkKSB7XG4gICAgICAgICAgaWYgKGNoaWxkLmNhbGxlZS50eXBlID09PSAnSW1wb3J0Jykge1xuICAgICAgICAgICAgcHJvY2Vzc0R5bmFtaWNJbXBvcnQoY2hpbGQuYXJndW1lbnRzWzBdKTtcbiAgICAgICAgICB9XG4gICAgICAgIH0sXG4gICAgICB9KTtcblxuICAgICAgbm9kZS5ib2R5LmZvckVhY2goKGFzdE5vZGUpID0+IHtcbiAgICAgICAgbGV0IHJlc29sdmVkUGF0aDtcblxuICAgICAgICAvLyBzdXBwb3J0IGZvciBleHBvcnQgeyB2YWx1ZSB9IGZyb20gJ21vZHVsZSdcbiAgICAgICAgaWYgKGFzdE5vZGUudHlwZSA9PT0gRVhQT1JUX05BTUVEX0RFQ0xBUkFUSU9OKSB7XG4gICAgICAgICAgaWYgKGFzdE5vZGUuc291cmNlKSB7XG4gICAgICAgICAgICByZXNvbHZlZFBhdGggPSByZXNvbHZlKGFzdE5vZGUuc291cmNlLnJhdy5yZXBsYWNlKC8oJ3xcIikvZywgJycpLCBjb250ZXh0KTtcbiAgICAgICAgICAgIGFzdE5vZGUuc3BlY2lmaWVycy5mb3JFYWNoKChzcGVjaWZpZXIpID0+IHtcbiAgICAgICAgICAgICAgY29uc3QgbmFtZSA9IHNwZWNpZmllci5sb2NhbC5uYW1lIHx8IHNwZWNpZmllci5sb2NhbC52YWx1ZTtcbiAgICAgICAgICAgICAgaWYgKG5hbWUgPT09IERFRkFVTFQpIHtcbiAgICAgICAgICAgICAgICBuZXdEZWZhdWx0SW1wb3J0cy5hZGQocmVzb2x2ZWRQYXRoKTtcbiAgICAgICAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICAgICAgICBuZXdJbXBvcnRzLnNldChuYW1lLCByZXNvbHZlZFBhdGgpO1xuICAgICAgICAgICAgICB9XG4gICAgICAgICAgICB9KTtcbiAgICAgICAgICB9XG4gICAgICAgIH1cblxuICAgICAgICBpZiAoYXN0Tm9kZS50eXBlID09PSBFWFBPUlRfQUxMX0RFQ0xBUkFUSU9OKSB7XG4gICAgICAgICAgcmVzb2x2ZWRQYXRoID0gcmVzb2x2ZShhc3ROb2RlLnNvdXJjZS5yYXcucmVwbGFjZSgvKCd8XCIpL2csICcnKSwgY29udGV4dCk7XG4gICAgICAgICAgbmV3RXhwb3J0QWxsLmFkZChyZXNvbHZlZFBhdGgpO1xuICAgICAgICB9XG5cbiAgICAgICAgaWYgKGFzdE5vZGUudHlwZSA9PT0gSU1QT1JUX0RFQ0xBUkFUSU9OKSB7XG4gICAgICAgICAgcmVzb2x2ZWRQYXRoID0gcmVzb2x2ZShhc3ROb2RlLnNvdXJjZS5yYXcucmVwbGFjZSgvKCd8XCIpL2csICcnKSwgY29udGV4dCk7XG4gICAgICAgICAgaWYgKCFyZXNvbHZlZFBhdGgpIHtcbiAgICAgICAgICAgIHJldHVybjtcbiAgICAgICAgICB9XG5cbiAgICAgICAgICBpZiAoaXNOb2RlTW9kdWxlKHJlc29sdmVkUGF0aCkpIHtcbiAgICAgICAgICAgIHJldHVybjtcbiAgICAgICAgICB9XG5cbiAgICAgICAgICBpZiAobmV3TmFtZXNwYWNlSW1wb3J0RXhpc3RzKGFzdE5vZGUuc3BlY2lmaWVycykpIHtcbiAgICAgICAgICAgIG5ld05hbWVzcGFjZUltcG9ydHMuYWRkKHJlc29sdmVkUGF0aCk7XG4gICAgICAgICAgfVxuXG4gICAgICAgICAgaWYgKG5ld0RlZmF1bHRJbXBvcnRFeGlzdHMoYXN0Tm9kZS5zcGVjaWZpZXJzKSkge1xuICAgICAgICAgICAgbmV3RGVmYXVsdEltcG9ydHMuYWRkKHJlc29sdmVkUGF0aCk7XG4gICAgICAgICAgfVxuXG4gICAgICAgICAgYXN0Tm9kZS5zcGVjaWZpZXJzXG4gICAgICAgICAgICAuZmlsdGVyKChzcGVjaWZpZXIpID0+IHNwZWNpZmllci50eXBlICE9PSBJTVBPUlRfREVGQVVMVF9TUEVDSUZJRVIgJiYgc3BlY2lmaWVyLnR5cGUgIT09IElNUE9SVF9OQU1FU1BBQ0VfU1BFQ0lGSUVSKVxuICAgICAgICAgICAgLmZvckVhY2goKHNwZWNpZmllcikgPT4ge1xuICAgICAgICAgICAgICBuZXdJbXBvcnRzLnNldChzcGVjaWZpZXIuaW1wb3J0ZWQubmFtZSB8fCBzcGVjaWZpZXIuaW1wb3J0ZWQudmFsdWUsIHJlc29sdmVkUGF0aCk7XG4gICAgICAgICAgICB9KTtcbiAgICAgICAgfVxuICAgICAgfSk7XG5cbiAgICAgIG5ld0V4cG9ydEFsbC5mb3JFYWNoKCh2YWx1ZSkgPT4ge1xuICAgICAgICBpZiAoIW9sZEV4cG9ydEFsbC5oYXModmFsdWUpKSB7XG4gICAgICAgICAgbGV0IGltcG9ydHMgPSBvbGRJbXBvcnRQYXRocy5nZXQodmFsdWUpO1xuICAgICAgICAgIGlmICh0eXBlb2YgaW1wb3J0cyA9PT0gJ3VuZGVmaW5lZCcpIHtcbiAgICAgICAgICAgIGltcG9ydHMgPSBuZXcgU2V0KCk7XG4gICAgICAgICAgfVxuICAgICAgICAgIGltcG9ydHMuYWRkKEVYUE9SVF9BTExfREVDTEFSQVRJT04pO1xuICAgICAgICAgIG9sZEltcG9ydFBhdGhzLnNldCh2YWx1ZSwgaW1wb3J0cyk7XG5cbiAgICAgICAgICBsZXQgZXhwb3J0cyA9IGV4cG9ydExpc3QuZ2V0KHZhbHVlKTtcbiAgICAgICAgICBsZXQgY3VycmVudEV4cG9ydDtcbiAgICAgICAgICBpZiAodHlwZW9mIGV4cG9ydHMgIT09ICd1bmRlZmluZWQnKSB7XG4gICAgICAgICAgICBjdXJyZW50RXhwb3J0ID0gZXhwb3J0cy5nZXQoRVhQT1JUX0FMTF9ERUNMQVJBVElPTik7XG4gICAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICAgIGV4cG9ydHMgPSBuZXcgTWFwKCk7XG4gICAgICAgICAgICBleHBvcnRMaXN0LnNldCh2YWx1ZSwgZXhwb3J0cyk7XG4gICAgICAgICAgfVxuXG4gICAgICAgICAgaWYgKHR5cGVvZiBjdXJyZW50RXhwb3J0ICE9PSAndW5kZWZpbmVkJykge1xuICAgICAgICAgICAgY3VycmVudEV4cG9ydC53aGVyZVVzZWQuYWRkKGZpbGUpO1xuICAgICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgICBjb25zdCB3aGVyZVVzZWQgPSBuZXcgU2V0KCk7XG4gICAgICAgICAgICB3aGVyZVVzZWQuYWRkKGZpbGUpO1xuICAgICAgICAgICAgZXhwb3J0cy5zZXQoRVhQT1JUX0FMTF9ERUNMQVJBVElPTiwgeyB3aGVyZVVzZWQgfSk7XG4gICAgICAgICAgfVxuICAgICAgICB9XG4gICAgICB9KTtcblxuICAgICAgb2xkRXhwb3J0QWxsLmZvckVhY2goKHZhbHVlKSA9PiB7XG4gICAgICAgIGlmICghbmV3RXhwb3J0QWxsLmhhcyh2YWx1ZSkpIHtcbiAgICAgICAgICBjb25zdCBpbXBvcnRzID0gb2xkSW1wb3J0UGF0aHMuZ2V0KHZhbHVlKTtcbiAgICAgICAgICBpbXBvcnRzLmRlbGV0ZShFWFBPUlRfQUxMX0RFQ0xBUkFUSU9OKTtcblxuICAgICAgICAgIGNvbnN0IGV4cG9ydHMgPSBleHBvcnRMaXN0LmdldCh2YWx1ZSk7XG4gICAgICAgICAgaWYgKHR5cGVvZiBleHBvcnRzICE9PSAndW5kZWZpbmVkJykge1xuICAgICAgICAgICAgY29uc3QgY3VycmVudEV4cG9ydCA9IGV4cG9ydHMuZ2V0KEVYUE9SVF9BTExfREVDTEFSQVRJT04pO1xuICAgICAgICAgICAgaWYgKHR5cGVvZiBjdXJyZW50RXhwb3J0ICE9PSAndW5kZWZpbmVkJykge1xuICAgICAgICAgICAgICBjdXJyZW50RXhwb3J0LndoZXJlVXNlZC5kZWxldGUoZmlsZSk7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgfVxuICAgICAgICB9XG4gICAgICB9KTtcblxuICAgICAgbmV3RGVmYXVsdEltcG9ydHMuZm9yRWFjaCgodmFsdWUpID0+IHtcbiAgICAgICAgaWYgKCFvbGREZWZhdWx0SW1wb3J0cy5oYXModmFsdWUpKSB7XG4gICAgICAgICAgbGV0IGltcG9ydHMgPSBvbGRJbXBvcnRQYXRocy5nZXQodmFsdWUpO1xuICAgICAgICAgIGlmICh0eXBlb2YgaW1wb3J0cyA9PT0gJ3VuZGVmaW5lZCcpIHtcbiAgICAgICAgICAgIGltcG9ydHMgPSBuZXcgU2V0KCk7XG4gICAgICAgICAgfVxuICAgICAgICAgIGltcG9ydHMuYWRkKElNUE9SVF9ERUZBVUxUX1NQRUNJRklFUik7XG4gICAgICAgICAgb2xkSW1wb3J0UGF0aHMuc2V0KHZhbHVlLCBpbXBvcnRzKTtcblxuICAgICAgICAgIGxldCBleHBvcnRzID0gZXhwb3J0TGlzdC5nZXQodmFsdWUpO1xuICAgICAgICAgIGxldCBjdXJyZW50RXhwb3J0O1xuICAgICAgICAgIGlmICh0eXBlb2YgZXhwb3J0cyAhPT0gJ3VuZGVmaW5lZCcpIHtcbiAgICAgICAgICAgIGN1cnJlbnRFeHBvcnQgPSBleHBvcnRzLmdldChJTVBPUlRfREVGQVVMVF9TUEVDSUZJRVIpO1xuICAgICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgICBleHBvcnRzID0gbmV3IE1hcCgpO1xuICAgICAgICAgICAgZXhwb3J0TGlzdC5zZXQodmFsdWUsIGV4cG9ydHMpO1xuICAgICAgICAgIH1cblxuICAgICAgICAgIGlmICh0eXBlb2YgY3VycmVudEV4cG9ydCAhPT0gJ3VuZGVmaW5lZCcpIHtcbiAgICAgICAgICAgIGN1cnJlbnRFeHBvcnQud2hlcmVVc2VkLmFkZChmaWxlKTtcbiAgICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgICAgY29uc3Qgd2hlcmVVc2VkID0gbmV3IFNldCgpO1xuICAgICAgICAgICAgd2hlcmVVc2VkLmFkZChmaWxlKTtcbiAgICAgICAgICAgIGV4cG9ydHMuc2V0KElNUE9SVF9ERUZBVUxUX1NQRUNJRklFUiwgeyB3aGVyZVVzZWQgfSk7XG4gICAgICAgICAgfVxuICAgICAgICB9XG4gICAgICB9KTtcblxuICAgICAgb2xkRGVmYXVsdEltcG9ydHMuZm9yRWFjaCgodmFsdWUpID0+IHtcbiAgICAgICAgaWYgKCFuZXdEZWZhdWx0SW1wb3J0cy5oYXModmFsdWUpKSB7XG4gICAgICAgICAgY29uc3QgaW1wb3J0cyA9IG9sZEltcG9ydFBhdGhzLmdldCh2YWx1ZSk7XG4gICAgICAgICAgaW1wb3J0cy5kZWxldGUoSU1QT1JUX0RFRkFVTFRfU1BFQ0lGSUVSKTtcblxuICAgICAgICAgIGNvbnN0IGV4cG9ydHMgPSBleHBvcnRMaXN0LmdldCh2YWx1ZSk7XG4gICAgICAgICAgaWYgKHR5cGVvZiBleHBvcnRzICE9PSAndW5kZWZpbmVkJykge1xuICAgICAgICAgICAgY29uc3QgY3VycmVudEV4cG9ydCA9IGV4cG9ydHMuZ2V0KElNUE9SVF9ERUZBVUxUX1NQRUNJRklFUik7XG4gICAgICAgICAgICBpZiAodHlwZW9mIGN1cnJlbnRFeHBvcnQgIT09ICd1bmRlZmluZWQnKSB7XG4gICAgICAgICAgICAgIGN1cnJlbnRFeHBvcnQud2hlcmVVc2VkLmRlbGV0ZShmaWxlKTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICB9XG4gICAgICAgIH1cbiAgICAgIH0pO1xuXG4gICAgICBuZXdOYW1lc3BhY2VJbXBvcnRzLmZvckVhY2goKHZhbHVlKSA9PiB7XG4gICAgICAgIGlmICghb2xkTmFtZXNwYWNlSW1wb3J0cy5oYXModmFsdWUpKSB7XG4gICAgICAgICAgbGV0IGltcG9ydHMgPSBvbGRJbXBvcnRQYXRocy5nZXQodmFsdWUpO1xuICAgICAgICAgIGlmICh0eXBlb2YgaW1wb3J0cyA9PT0gJ3VuZGVmaW5lZCcpIHtcbiAgICAgICAgICAgIGltcG9ydHMgPSBuZXcgU2V0KCk7XG4gICAgICAgICAgfVxuICAgICAgICAgIGltcG9ydHMuYWRkKElNUE9SVF9OQU1FU1BBQ0VfU1BFQ0lGSUVSKTtcbiAgICAgICAgICBvbGRJbXBvcnRQYXRocy5zZXQodmFsdWUsIGltcG9ydHMpO1xuXG4gICAgICAgICAgbGV0IGV4cG9ydHMgPSBleHBvcnRMaXN0LmdldCh2YWx1ZSk7XG4gICAgICAgICAgbGV0IGN1cnJlbnRFeHBvcnQ7XG4gICAgICAgICAgaWYgKHR5cGVvZiBleHBvcnRzICE9PSAndW5kZWZpbmVkJykge1xuICAgICAgICAgICAgY3VycmVudEV4cG9ydCA9IGV4cG9ydHMuZ2V0KElNUE9SVF9OQU1FU1BBQ0VfU1BFQ0lGSUVSKTtcbiAgICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgICAgZXhwb3J0cyA9IG5ldyBNYXAoKTtcbiAgICAgICAgICAgIGV4cG9ydExpc3Quc2V0KHZhbHVlLCBleHBvcnRzKTtcbiAgICAgICAgICB9XG5cbiAgICAgICAgICBpZiAodHlwZW9mIGN1cnJlbnRFeHBvcnQgIT09ICd1bmRlZmluZWQnKSB7XG4gICAgICAgICAgICBjdXJyZW50RXhwb3J0LndoZXJlVXNlZC5hZGQoZmlsZSk7XG4gICAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICAgIGNvbnN0IHdoZXJlVXNlZCA9IG5ldyBTZXQoKTtcbiAgICAgICAgICAgIHdoZXJlVXNlZC5hZGQoZmlsZSk7XG4gICAgICAgICAgICBleHBvcnRzLnNldChJTVBPUlRfTkFNRVNQQUNFX1NQRUNJRklFUiwgeyB3aGVyZVVzZWQgfSk7XG4gICAgICAgICAgfVxuICAgICAgICB9XG4gICAgICB9KTtcblxuICAgICAgb2xkTmFtZXNwYWNlSW1wb3J0cy5mb3JFYWNoKCh2YWx1ZSkgPT4ge1xuICAgICAgICBpZiAoIW5ld05hbWVzcGFjZUltcG9ydHMuaGFzKHZhbHVlKSkge1xuICAgICAgICAgIGNvbnN0IGltcG9ydHMgPSBvbGRJbXBvcnRQYXRocy5nZXQodmFsdWUpO1xuICAgICAgICAgIGltcG9ydHMuZGVsZXRlKElNUE9SVF9OQU1FU1BBQ0VfU1BFQ0lGSUVSKTtcblxuICAgICAgICAgIGNvbnN0IGV4cG9ydHMgPSBleHBvcnRMaXN0LmdldCh2YWx1ZSk7XG4gICAgICAgICAgaWYgKHR5cGVvZiBleHBvcnRzICE9PSAndW5kZWZpbmVkJykge1xuICAgICAgICAgICAgY29uc3QgY3VycmVudEV4cG9ydCA9IGV4cG9ydHMuZ2V0KElNUE9SVF9OQU1FU1BBQ0VfU1BFQ0lGSUVSKTtcbiAgICAgICAgICAgIGlmICh0eXBlb2YgY3VycmVudEV4cG9ydCAhPT0gJ3VuZGVmaW5lZCcpIHtcbiAgICAgICAgICAgICAgY3VycmVudEV4cG9ydC53aGVyZVVzZWQuZGVsZXRlKGZpbGUpO1xuICAgICAgICAgICAgfVxuICAgICAgICAgIH1cbiAgICAgICAgfVxuICAgICAgfSk7XG5cbiAgICAgIG5ld0ltcG9ydHMuZm9yRWFjaCgodmFsdWUsIGtleSkgPT4ge1xuICAgICAgICBpZiAoIW9sZEltcG9ydHMuaGFzKGtleSkpIHtcbiAgICAgICAgICBsZXQgaW1wb3J0cyA9IG9sZEltcG9ydFBhdGhzLmdldCh2YWx1ZSk7XG4gICAgICAgICAgaWYgKHR5cGVvZiBpbXBvcnRzID09PSAndW5kZWZpbmVkJykge1xuICAgICAgICAgICAgaW1wb3J0cyA9IG5ldyBTZXQoKTtcbiAgICAgICAgICB9XG4gICAgICAgICAgaW1wb3J0cy5hZGQoa2V5KTtcbiAgICAgICAgICBvbGRJbXBvcnRQYXRocy5zZXQodmFsdWUsIGltcG9ydHMpO1xuXG4gICAgICAgICAgbGV0IGV4cG9ydHMgPSBleHBvcnRMaXN0LmdldCh2YWx1ZSk7XG4gICAgICAgICAgbGV0IGN1cnJlbnRFeHBvcnQ7XG4gICAgICAgICAgaWYgKHR5cGVvZiBleHBvcnRzICE9PSAndW5kZWZpbmVkJykge1xuICAgICAgICAgICAgY3VycmVudEV4cG9ydCA9IGV4cG9ydHMuZ2V0KGtleSk7XG4gICAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICAgIGV4cG9ydHMgPSBuZXcgTWFwKCk7XG4gICAgICAgICAgICBleHBvcnRMaXN0LnNldCh2YWx1ZSwgZXhwb3J0cyk7XG4gICAgICAgICAgfVxuXG4gICAgICAgICAgaWYgKHR5cGVvZiBjdXJyZW50RXhwb3J0ICE9PSAndW5kZWZpbmVkJykge1xuICAgICAgICAgICAgY3VycmVudEV4cG9ydC53aGVyZVVzZWQuYWRkKGZpbGUpO1xuICAgICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgICBjb25zdCB3aGVyZVVzZWQgPSBuZXcgU2V0KCk7XG4gICAgICAgICAgICB3aGVyZVVzZWQuYWRkKGZpbGUpO1xuICAgICAgICAgICAgZXhwb3J0cy5zZXQoa2V5LCB7IHdoZXJlVXNlZCB9KTtcbiAgICAgICAgICB9XG4gICAgICAgIH1cbiAgICAgIH0pO1xuXG4gICAgICBvbGRJbXBvcnRzLmZvckVhY2goKHZhbHVlLCBrZXkpID0+IHtcbiAgICAgICAgaWYgKCFuZXdJbXBvcnRzLmhhcyhrZXkpKSB7XG4gICAgICAgICAgY29uc3QgaW1wb3J0cyA9IG9sZEltcG9ydFBhdGhzLmdldCh2YWx1ZSk7XG4gICAgICAgICAgaW1wb3J0cy5kZWxldGUoa2V5KTtcblxuICAgICAgICAgIGNvbnN0IGV4cG9ydHMgPSBleHBvcnRMaXN0LmdldCh2YWx1ZSk7XG4gICAgICAgICAgaWYgKHR5cGVvZiBleHBvcnRzICE9PSAndW5kZWZpbmVkJykge1xuICAgICAgICAgICAgY29uc3QgY3VycmVudEV4cG9ydCA9IGV4cG9ydHMuZ2V0KGtleSk7XG4gICAgICAgICAgICBpZiAodHlwZW9mIGN1cnJlbnRFeHBvcnQgIT09ICd1bmRlZmluZWQnKSB7XG4gICAgICAgICAgICAgIGN1cnJlbnRFeHBvcnQud2hlcmVVc2VkLmRlbGV0ZShmaWxlKTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICB9XG4gICAgICAgIH1cbiAgICAgIH0pO1xuICAgIH07XG5cbiAgICByZXR1cm4ge1xuICAgICAgJ1Byb2dyYW06ZXhpdCcobm9kZSkge1xuICAgICAgICB1cGRhdGVFeHBvcnRVc2FnZShub2RlKTtcbiAgICAgICAgdXBkYXRlSW1wb3J0VXNhZ2Uobm9kZSk7XG4gICAgICAgIGNoZWNrRXhwb3J0UHJlc2VuY2Uobm9kZSk7XG4gICAgICB9LFxuICAgICAgRXhwb3J0RGVmYXVsdERlY2xhcmF0aW9uKG5vZGUpIHtcbiAgICAgICAgY2hlY2tVc2FnZShub2RlLCBJTVBPUlRfREVGQVVMVF9TUEVDSUZJRVIsIGZhbHNlKTtcbiAgICAgIH0sXG4gICAgICBFeHBvcnROYW1lZERlY2xhcmF0aW9uKG5vZGUpIHtcbiAgICAgICAgbm9kZS5zcGVjaWZpZXJzLmZvckVhY2goKHNwZWNpZmllcikgPT4ge1xuICAgICAgICAgIGNoZWNrVXNhZ2Uoc3BlY2lmaWVyLCBzcGVjaWZpZXIuZXhwb3J0ZWQubmFtZSB8fCBzcGVjaWZpZXIuZXhwb3J0ZWQudmFsdWUsIGZhbHNlKTtcbiAgICAgICAgfSk7XG4gICAgICAgIGZvckVhY2hEZWNsYXJhdGlvbklkZW50aWZpZXIobm9kZS5kZWNsYXJhdGlvbiwgKG5hbWUsIGlzVHlwZUV4cG9ydCkgPT4ge1xuICAgICAgICAgIGNoZWNrVXNhZ2Uobm9kZSwgbmFtZSwgaXNUeXBlRXhwb3J0KTtcbiAgICAgICAgfSk7XG4gICAgICB9LFxuICAgIH07XG4gIH0sXG59O1xuIl19