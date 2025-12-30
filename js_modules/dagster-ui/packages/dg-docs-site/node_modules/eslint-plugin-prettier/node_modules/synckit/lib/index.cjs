'use strict';

var node_crypto = require('node:crypto');
var fs = require('node:fs');
var module$1 = require('node:module');
var path = require('node:path');
var node_url = require('node:url');
var node_worker_threads = require('node:worker_threads');
var core = require('@pkgr/core');

var __defProp = Object.defineProperty;
var __getOwnPropSymbols = Object.getOwnPropertySymbols;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __propIsEnum = Object.prototype.propertyIsEnumerable;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues = (a, b) => {
  for (var prop in b || (b = {}))
    if (__hasOwnProp.call(b, prop))
      __defNormalProp(a, prop, b[prop]);
  if (__getOwnPropSymbols)
    for (var prop of __getOwnPropSymbols(b)) {
      if (__propIsEnum.call(b, prop))
        __defNormalProp(a, prop, b[prop]);
    }
  return a;
};
var __objRest = (source, exclude) => {
  var target = {};
  for (var prop in source)
    if (__hasOwnProp.call(source, prop) && exclude.indexOf(prop) < 0)
      target[prop] = source[prop];
  if (source != null && __getOwnPropSymbols)
    for (var prop of __getOwnPropSymbols(source)) {
      if (exclude.indexOf(prop) < 0 && __propIsEnum.call(source, prop))
        target[prop] = source[prop];
    }
  return target;
};
var __async = (__this, __arguments, generator) => {
  return new Promise((resolve, reject) => {
    var fulfilled = (value) => {
      try {
        step(generator.next(value));
      } catch (e) {
        reject(e);
      }
    };
    var rejected = (value) => {
      try {
        step(generator.throw(value));
      } catch (e) {
        reject(e);
      }
    };
    var step = (x) => x.done ? resolve(x.value) : Promise.resolve(x.value).then(fulfilled, rejected);
    step((generator = generator.apply(__this, __arguments)).next());
  });
};
const import_meta = {};
const INT32_BYTES = 4;
const TsRunner = {
  // https://nodejs.org/docs/latest/api/typescript.html#type-stripping
  Node: "node",
  // https://bun.sh/docs/typescript
  Bun: "bun",
  // https://github.com/TypeStrong/ts-node
  TsNode: "ts-node",
  // https://github.com/egoist/esbuild-register
  EsbuildRegister: "esbuild-register",
  // https://github.com/folke/esbuild-runner
  EsbuildRunner: "esbuild-runner",
  // https://github.com/swc-project/swc-node/tree/master/packages/register
  SWC: "swc",
  // https://github.com/esbuild-kit/tsx
  TSX: "tsx"
};
const {
  NODE_OPTIONS: NODE_OPTIONS_ = "",
  SYNCKIT_EXEC_ARGV = "",
  SYNCKIT_GLOBAL_SHIMS,
  SYNCKIT_TIMEOUT,
  SYNCKIT_TS_RUNNER
} = process.env;
const MTS_SUPPORTED_NODE_VERSION = "16";
const LOADER_SUPPORTED_NODE_VERSION = "20";
const STRIP_TYPES_NODE_VERSION = "22.6";
const TRANSFORM_TYPES_NODE_VERSION = "22.7";
const FEATURE_TYPESCRIPT_NODE_VERSION = "22.10";
const DEFAULT_TYPES_NODE_VERSION = "23.6";
const STRIP_TYPES_FLAG = "--experimental-strip-types";
const TRANSFORM_TYPES_FLAG = "--experimental-transform-types";
const NO_STRIP_TYPES_FLAG = "--no-experimental-strip-types";
const NODE_OPTIONS = NODE_OPTIONS_.split(/\s+/);
const hasFlag = (flag) => NODE_OPTIONS.includes(flag) || process.argv.includes(flag);
const parseVersion = (version) => version.split(".").map(Number.parseFloat);
const compareVersion = (version1, version2) => {
  const versions1 = parseVersion(version1);
  const versions2 = parseVersion(version2);
  const length = Math.max(versions1.length, versions2.length);
  for (let i = 0; i < length; i++) {
    const v1 = versions1[i] || 0;
    const v2 = versions2[i] || 0;
    if (v1 > v2) {
      return 1;
    }
    if (v1 < v2) {
      return -1;
    }
  }
  return 0;
};
const NODE_VERSION = process.versions.node;
const NO_STRIP_TYPES = (
  // >=
  compareVersion(NODE_VERSION, FEATURE_TYPESCRIPT_NODE_VERSION) >= 0 ? process.features.typescript === false : hasFlag(NO_STRIP_TYPES_FLAG) && !hasFlag(STRIP_TYPES_FLAG) && !hasFlag(TRANSFORM_TYPES_FLAG)
);
const DEFAULT_TIMEOUT = SYNCKIT_TIMEOUT ? +SYNCKIT_TIMEOUT : void 0;
const DEFAULT_EXEC_ARGV = SYNCKIT_EXEC_ARGV.split(",");
const DEFAULT_TS_RUNNER = SYNCKIT_TS_RUNNER;
const DEFAULT_GLOBAL_SHIMS = ["1", "true"].includes(
  SYNCKIT_GLOBAL_SHIMS
);
const DEFAULT_GLOBAL_SHIMS_PRESET = [
  {
    moduleName: "node-fetch",
    globalName: "fetch"
  },
  {
    moduleName: "node:perf_hooks",
    globalName: "performance",
    named: "performance"
  }
];
let syncFnCache;
function extractProperties(object) {
  if (object && typeof object === "object") {
    const properties = {};
    for (const key in object) {
      properties[key] = object[key];
    }
    return properties;
  }
}
function createSyncFn(workerPath, timeoutOrOptions) {
  syncFnCache != null ? syncFnCache : syncFnCache = /* @__PURE__ */ new Map();
  if (typeof workerPath !== "string" || workerPath.startsWith("file://")) {
    workerPath = node_url.fileURLToPath(workerPath);
  }
  const cachedSyncFn = syncFnCache.get(workerPath);
  if (cachedSyncFn) {
    return cachedSyncFn;
  }
  if (!path.isAbsolute(workerPath)) {
    throw new Error("`workerPath` must be absolute");
  }
  const syncFn = startWorkerThread(
    workerPath,
    /* istanbul ignore next */
    typeof timeoutOrOptions === "number" ? { timeout: timeoutOrOptions } : timeoutOrOptions
  );
  syncFnCache.set(workerPath, syncFn);
  return syncFn;
}
const dataUrl = (code) => new URL(`data:text/javascript,${encodeURIComponent(code)}`);
const isFile = (path2) => {
  var _a;
  try {
    return !!((_a = fs.statSync(path2, { throwIfNoEntry: false })) == null ? void 0 : _a.isFile());
  } catch (e) {
    return false;
  }
};
const setupTsRunner = (workerPath, { execArgv, tsRunner }) => {
  let ext = path.extname(workerPath);
  if (!/([/\\])node_modules\1/.test(workerPath) && (!ext || /^\.[cm]?js$/.test(ext))) {
    const workPathWithoutExt = ext ? workerPath.slice(0, -ext.length) : workerPath;
    let extensions;
    switch (ext) {
      case ".cjs": {
        extensions = [".cts", ".cjs"];
        break;
      }
      case ".mjs": {
        extensions = [".mts", ".mjs"];
        break;
      }
      default: {
        extensions = [".ts", ".js"];
        break;
      }
    }
    const found = core.tryExtensions(workPathWithoutExt, extensions);
    let differentExt;
    if (found && (!ext || (differentExt = found !== workPathWithoutExt))) {
      workerPath = found;
      if (differentExt) {
        ext = path.extname(workerPath);
      }
    }
  }
  const isTs = /\.[cm]?ts$/.test(workerPath);
  let jsUseEsm = workerPath.endsWith(".mjs");
  let tsUseEsm = workerPath.endsWith(".mts");
  if (isTs) {
    if (!tsUseEsm) {
      const pkg = core.findUp(workerPath);
      if (pkg) {
        tsUseEsm = core.cjsRequire(pkg).type === "module";
      }
    }
    const stripTypesIndex = execArgv.indexOf(STRIP_TYPES_FLAG);
    const transformTypesIndex = execArgv.indexOf(TRANSFORM_TYPES_FLAG);
    const noStripTypesIndex = execArgv.indexOf(NO_STRIP_TYPES_FLAG);
    const execArgvNoStripTypes = noStripTypesIndex > stripTypesIndex || noStripTypesIndex > transformTypesIndex;
    const noStripTypes = execArgvNoStripTypes || stripTypesIndex === -1 && transformTypesIndex === -1 && NO_STRIP_TYPES;
    if (tsRunner == null) {
      if (process.versions.bun) {
        tsRunner = TsRunner.Bun;
      } else if (!noStripTypes && // >=
      compareVersion(NODE_VERSION, STRIP_TYPES_NODE_VERSION) >= 0) {
        tsRunner = TsRunner.Node;
      } else if (core.isPkgAvailable(TsRunner.TsNode)) {
        tsRunner = TsRunner.TsNode;
      }
    }
    switch (tsRunner) {
      case TsRunner.Bun: {
        break;
      }
      case TsRunner.Node: {
        if (compareVersion(NODE_VERSION, STRIP_TYPES_NODE_VERSION) < 0) {
          throw new Error(
            "type stripping is not supported in this node version"
          );
        }
        if (noStripTypes) {
          throw new Error("type stripping is disabled explicitly");
        }
        if (compareVersion(NODE_VERSION, DEFAULT_TYPES_NODE_VERSION) >= 0) {
          break;
        }
        if (
          // >=
          compareVersion(NODE_VERSION, TRANSFORM_TYPES_NODE_VERSION) >= 0 && !execArgv.includes(TRANSFORM_TYPES_FLAG)
        ) {
          execArgv = [TRANSFORM_TYPES_FLAG, ...execArgv];
        } else if (
          // >=
          compareVersion(NODE_VERSION, STRIP_TYPES_NODE_VERSION) >= 0 && !execArgv.includes(STRIP_TYPES_FLAG)
        ) {
          execArgv = [STRIP_TYPES_FLAG, ...execArgv];
        }
        break;
      }
      case TsRunner.TsNode: {
        if (tsUseEsm) {
          if (!execArgv.includes("--loader")) {
            execArgv = ["--loader", `${TsRunner.TsNode}/esm`, ...execArgv];
          }
        } else if (!execArgv.includes("-r")) {
          execArgv = ["-r", `${TsRunner.TsNode}/register`, ...execArgv];
        }
        break;
      }
      case TsRunner.EsbuildRegister: {
        if (!execArgv.includes("-r")) {
          execArgv = ["-r", TsRunner.EsbuildRegister, ...execArgv];
        }
        break;
      }
      case TsRunner.EsbuildRunner: {
        if (!execArgv.includes("-r")) {
          execArgv = ["-r", `${TsRunner.EsbuildRunner}/register`, ...execArgv];
        }
        break;
      }
      case TsRunner.SWC: {
        if (!execArgv.includes("-r")) {
          execArgv = ["-r", `@${TsRunner.SWC}-node/register`, ...execArgv];
        }
        break;
      }
      case TsRunner.TSX: {
        if (!execArgv.includes("--loader")) {
          execArgv = ["--loader", TsRunner.TSX, ...execArgv];
        }
        break;
      }
      default: {
        throw new Error(`Unknown ts runner: ${String(tsRunner)}`);
      }
    }
  } else if (!jsUseEsm) {
    const pkg = core.findUp(workerPath);
    if (pkg) {
      jsUseEsm = core.cjsRequire(pkg).type === "module";
    }
  }
  let resolvedPnpLoaderPath;
  if (process.versions.pnp) {
    let pnpApiPath;
    try {
      pnpApiPath = core.cjsRequire.resolve("pnpapi");
    } catch (e) {
    }
    if (pnpApiPath && !NODE_OPTIONS.some(
      (option, index) => ["-r", "--require"].includes(option) && pnpApiPath === core.cjsRequire.resolve(NODE_OPTIONS[index + 1])
    ) && !execArgv.includes(pnpApiPath)) {
      execArgv = ["-r", pnpApiPath, ...execArgv];
      const pnpLoaderPath = path.resolve(pnpApiPath, "../.pnp.loader.mjs");
      if (isFile(pnpLoaderPath)) {
        resolvedPnpLoaderPath = node_url.pathToFileURL(pnpLoaderPath).toString();
        if (compareVersion(NODE_VERSION, LOADER_SUPPORTED_NODE_VERSION) < 0) {
          execArgv = [
            "--experimental-loader",
            resolvedPnpLoaderPath,
            ...execArgv
          ];
        }
      }
    }
  }
  return {
    ext,
    isTs,
    jsUseEsm,
    tsRunner,
    tsUseEsm,
    workerPath,
    pnpLoaderPath: resolvedPnpLoaderPath,
    execArgv
  };
};
const md5Hash = (text) => (
  // eslint-disable-next-line sonarjs/hashing
  node_crypto.createHash("md5").update(text).digest("hex")
);
const encodeImportModule = (moduleNameOrGlobalShim, type = "import") => {
  const { moduleName, globalName, named, conditional } = typeof moduleNameOrGlobalShim === "string" ? { moduleName: moduleNameOrGlobalShim } : moduleNameOrGlobalShim;
  const importStatement = type === "import" ? `import${globalName ? " " + (named === null ? "* as " + globalName : (named == null ? void 0 : named.trim()) ? `{${named}}` : globalName) + " from" : ""} '${path.isAbsolute(moduleName) ? String(node_url.pathToFileURL(moduleName)) : moduleName}'` : `${globalName ? "const " + ((named == null ? void 0 : named.trim()) ? `{${named}}` : globalName) + "=" : ""}require('${moduleName.replace(/\\/g, "\\\\")}')`;
  if (!globalName) {
    return importStatement;
  }
  const overrideStatement = `globalThis.${globalName}=${(named == null ? void 0 : named.trim()) ? named : globalName}`;
  return importStatement + (conditional === false ? `;${overrideStatement}` : `;if(!globalThis.${globalName})${overrideStatement}`);
};
const _generateGlobals = (globalShims, type) => globalShims.reduce(
  (acc, shim) => `${acc}${acc ? ";" : ""}${encodeImportModule(shim, type)}`,
  ""
);
let globalsCache;
let tmpdir;
const _dirname = typeof __dirname === "undefined" ? path.dirname(node_url.fileURLToPath(import_meta.url)) : (
  /* istanbul ignore next */
  __dirname
);
let sharedBuffer;
let sharedBufferView;
const generateGlobals = (workerPath, globalShims, type = "import") => {
  if (globalShims.length === 0) {
    return "";
  }
  globalsCache != null ? globalsCache : globalsCache = /* @__PURE__ */ new Map();
  const cached = globalsCache.get(workerPath);
  if (cached) {
    const [content2, filepath2] = cached;
    if (type === "require" && !filepath2 || type === "import" && filepath2 && isFile(filepath2)) {
      return content2;
    }
  }
  const globals = _generateGlobals(globalShims, type);
  let content = globals;
  let filepath;
  if (type === "import") {
    if (!tmpdir) {
      tmpdir = path.resolve(core.findUp(_dirname), "../node_modules/.synckit");
    }
    fs.mkdirSync(tmpdir, { recursive: true });
    filepath = path.resolve(tmpdir, md5Hash(workerPath) + ".mjs");
    content = encodeImportModule(filepath);
    fs.writeFileSync(filepath, globals);
  }
  globalsCache.set(workerPath, [content, filepath]);
  return content;
};
function startWorkerThread(workerPath, {
  timeout = DEFAULT_TIMEOUT,
  execArgv = DEFAULT_EXEC_ARGV,
  tsRunner = DEFAULT_TS_RUNNER,
  transferList = [],
  globalShims = DEFAULT_GLOBAL_SHIMS
} = {}) {
  const { port1: mainPort, port2: workerPort } = new node_worker_threads.MessageChannel();
  const {
    isTs,
    ext,
    jsUseEsm,
    tsUseEsm,
    tsRunner: finalTsRunner,
    workerPath: finalWorkerPath,
    pnpLoaderPath,
    execArgv: finalExecArgv
  } = setupTsRunner(workerPath, { execArgv, tsRunner });
  const workerPathUrl = node_url.pathToFileURL(finalWorkerPath);
  if (/\.[cm]ts$/.test(finalWorkerPath)) {
    const isTsxSupported = !tsUseEsm || // >=
    compareVersion(NODE_VERSION, MTS_SUPPORTED_NODE_VERSION) >= 0;
    if (!finalTsRunner) {
      throw new Error("No ts runner specified, ts worker path is not supported");
    } else if ([
      // https://github.com/egoist/esbuild-register/issues/79
      TsRunner.EsbuildRegister,
      // https://github.com/folke/esbuild-runner/issues/67
      TsRunner.EsbuildRunner,
      // https://github.com/swc-project/swc-node/issues/667
      TsRunner.SWC,
      .../* istanbul ignore next */
      isTsxSupported ? [] : [TsRunner.TSX]
    ].includes(finalTsRunner)) {
      throw new Error(
        `${finalTsRunner} is not supported for ${ext} files yet` + /* istanbul ignore next */
        (isTsxSupported ? ", you can try [tsx](https://github.com/esbuild-kit/tsx) instead" : "")
      );
    }
  }
  const finalGlobalShims = (globalShims === true ? DEFAULT_GLOBAL_SHIMS_PRESET : Array.isArray(globalShims) ? globalShims : []).filter(({ moduleName }) => core.isPkgAvailable(moduleName));
  sharedBufferView != null ? sharedBufferView : sharedBufferView = new Int32Array(
    /* istanbul ignore next */
    sharedBuffer != null ? sharedBuffer : sharedBuffer = new SharedArrayBuffer(
      INT32_BYTES
    ),
    0,
    1
  );
  const useGlobals = finalGlobalShims.length > 0;
  const useEval = isTs ? !tsUseEsm : !jsUseEsm && useGlobals;
  const worker = new node_worker_threads.Worker(
    jsUseEsm && useGlobals || tsUseEsm && finalTsRunner === TsRunner.TsNode ? dataUrl(
      `${generateGlobals(
        finalWorkerPath,
        finalGlobalShims
      )};import '${String(workerPathUrl)}'`
    ) : useEval ? `${generateGlobals(
      finalWorkerPath,
      finalGlobalShims,
      "require"
    )};${encodeImportModule(finalWorkerPath, "require")}` : workerPathUrl,
    {
      eval: useEval,
      workerData: { sharedBufferView, workerPort, pnpLoaderPath },
      transferList: [workerPort, ...transferList],
      execArgv: finalExecArgv
    }
  );
  let nextID = 0;
  const receiveMessageWithId = (port, expectedId, waitingTimeout) => {
    const start = Date.now();
    const status = Atomics.wait(sharedBufferView, 0, 0, waitingTimeout);
    Atomics.store(sharedBufferView, 0, 0);
    if (!["ok", "not-equal"].includes(status)) {
      const abortMsg = {
        id: expectedId,
        cmd: "abort"
      };
      port.postMessage(abortMsg);
      throw new Error("Internal error: Atomics.wait() failed: " + status);
    }
    const _a = node_worker_threads.receiveMessageOnPort(mainPort).message, { id } = _a, message = __objRest(_a, ["id"]);
    if (id < expectedId) {
      const waitingTime = Date.now() - start;
      return receiveMessageWithId(
        port,
        expectedId,
        waitingTimeout ? waitingTimeout - waitingTime : void 0
      );
    }
    if (expectedId !== id) {
      throw new Error(
        `Internal error: Expected id ${expectedId} but got id ${id}`
      );
    }
    return __spreadValues({ id }, message);
  };
  const syncFn = (...args) => {
    const id = nextID++;
    const msg = { id, args };
    worker.postMessage(msg);
    const { result, error, properties, stdio } = receiveMessageWithId(
      mainPort,
      id,
      timeout
    );
    for (const { type, chunk, encoding } of stdio) {
      process[type].write(chunk, encoding);
    }
    if (error) {
      throw Object.assign(error, properties);
    }
    return result;
  };
  worker.unref();
  return syncFn;
}
function runAsWorker(fn) {
  if (!node_worker_threads.workerData) {
    return;
  }
  const stdio = [];
  for (const type of ["stdout", "stderr"]) {
    process[type]._writev = (chunks, callback) => {
      for (const {
        // type-coverage:ignore-next-line -- we can't control
        chunk,
        encoding
      } of chunks) {
        stdio.push({
          type,
          // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment -- we can't control
          chunk,
          encoding
        });
      }
      callback();
    };
  }
  const { workerPort, sharedBufferView: sharedBufferView2, pnpLoaderPath } = node_worker_threads.workerData;
  if (pnpLoaderPath && // >=
  compareVersion(NODE_VERSION, LOADER_SUPPORTED_NODE_VERSION) >= 0) {
    module$1.register(pnpLoaderPath);
  }
  node_worker_threads.parentPort.on(
    "message",
    ({ id, args }) => {
      (() => __async(this, null, function* () {
        let isAborted = false;
        const handleAbortMessage = (msg2) => {
          if (msg2.id === id && msg2.cmd === "abort") {
            isAborted = true;
          }
        };
        workerPort.on("message", handleAbortMessage);
        let msg;
        try {
          msg = { id, stdio, result: yield fn(...args) };
        } catch (error) {
          msg = { id, stdio, error, properties: extractProperties(error) };
        }
        workerPort.off("message", handleAbortMessage);
        if (isAborted) {
          stdio.length = 0;
          return;
        }
        try {
          workerPort.postMessage(msg);
          Atomics.add(sharedBufferView2, 0, 1);
          Atomics.notify(sharedBufferView2, 0);
        } finally {
          stdio.length = 0;
        }
      }))();
    }
  );
}

exports.DEFAULT_EXEC_ARGV = DEFAULT_EXEC_ARGV;
exports.DEFAULT_GLOBAL_SHIMS = DEFAULT_GLOBAL_SHIMS;
exports.DEFAULT_GLOBAL_SHIMS_PRESET = DEFAULT_GLOBAL_SHIMS_PRESET;
exports.DEFAULT_TIMEOUT = DEFAULT_TIMEOUT;
exports.DEFAULT_TS_RUNNER = DEFAULT_TS_RUNNER;
exports.DEFAULT_TYPES_NODE_VERSION = DEFAULT_TYPES_NODE_VERSION;
exports.FEATURE_TYPESCRIPT_NODE_VERSION = FEATURE_TYPESCRIPT_NODE_VERSION;
exports.LOADER_SUPPORTED_NODE_VERSION = LOADER_SUPPORTED_NODE_VERSION;
exports.MTS_SUPPORTED_NODE_VERSION = MTS_SUPPORTED_NODE_VERSION;
exports.NODE_VERSION = NODE_VERSION;
exports.NO_STRIP_TYPES_FLAG = NO_STRIP_TYPES_FLAG;
exports.STRIP_TYPES_FLAG = STRIP_TYPES_FLAG;
exports.STRIP_TYPES_NODE_VERSION = STRIP_TYPES_NODE_VERSION;
exports.TRANSFORM_TYPES_FLAG = TRANSFORM_TYPES_FLAG;
exports.TRANSFORM_TYPES_NODE_VERSION = TRANSFORM_TYPES_NODE_VERSION;
exports.TsRunner = TsRunner;
exports._generateGlobals = _generateGlobals;
exports.compareVersion = compareVersion;
exports.createSyncFn = createSyncFn;
exports.encodeImportModule = encodeImportModule;
exports.extractProperties = extractProperties;
exports.generateGlobals = generateGlobals;
exports.isFile = isFile;
exports.runAsWorker = runAsWorker;
