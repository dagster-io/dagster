const puppeteer = require("puppeteer");
const { toMatchImageSnapshot } = require("jest-image-snapshot");
const { spawn } = require("child_process");
const sleep = require("await-sleep");

expect.extend({ toMatchImageSnapshot });

const screenshotPath = (pathFragment) =>
  __dirname + "/next/public/assets/images/tutorial/" + pathFragment;

const runDagit = async (args, port, dir, subdir) => {
  const dagitArgs = args.concat(["-p", port || 3000]);

  dagit = spawn("dagit", dagitArgs, {
    cwd: `../examples/docs_snippets/docs_snippets/intro_tutorial/${dir}/${subdir}/`,
  });

  console.log(`Running: "dagit ${dagitArgs.join(" ")}" on pid ${dagit.pid}`);

  dagit.stdout.on("data", (data) => {
    console.log(`dagit stdout: ${data}`);
  });

  dagit.stderr.on("data", (data) => {
    console.error(`dagit stderr: ${data}`);
  });

  dagit.on("close", (code) => {
    console.log(`dagit child process exited with code ${code}`);
  });

  dagit.on("error", (err) => {
    console.error("Failed to start subprocess.");
  });

  await sleep(5000);

  return port;
};

const tearDownDagit = async (ps) => {
  dagit.removeAllListeners("close");
  dagit.kill();

  await sleep(5000);

  return;
};

setConfig = (filename) => ({
  failureThreshold: "0.01",
  failureThresholdType: "percent",
  customSnapshotIdentifier: filename,
  customSnapshotsDir: "__generated__/",
  customDiffDir: "__generated__/",
});

describe("for hello_solid, hello_pipeline, and execute_pipeline", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f hello_cereal.py -a hello_cereal_pipeline
    dagit = await runDagit(["-f", "hello_cereal.py", "-a", "hello_cereal_pipeline"], 3000, "basics", "e01_first_pipeline");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    browser.removeAllListeners("targetcreated");
    done();
  });

  it("renders the pipelines view for the hello cereal pipeline", async () => {
    await page.goto("http://127.0.0.1:3000/pipeline/hello_cereal_pipeline/", {
      waitUntil: "networkidle2",
    });
    const image = await page.screenshot({
      path: screenshotPath("/hello_cereal_figure_one.png"), // picture in docs
    });
    expect(image).toMatchImageSnapshot(setConfig("hello_cereal_figure_one")); // snapshot
    return;
  });

  it("renders the playground for the hello cereal pipeline", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__hello_cereal_pipeline@hello_cereal.py:hello_cereal_pipeline/pipelines/hello_cereal_pipeline/playground", {
      waitUntil: "networkidle2",
    });

    const image = await page.screenshot({
      path: screenshotPath("/hello_cereal_figure_two.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("hello_cereal_figure_two"));
    return;
  });

  it("renders the executed playground view for the hello cereal pipeline", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__hello_cereal_pipeline@hello_cereal.py:hello_cereal_pipeline/pipelines/hello_cereal_pipeline/playground", {
      waitUntil: "networkidle2",
    });

    const executeButton = await page.waitForSelector(
      'button[type="button"][status="ready"]'
    );
    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          const pages = await browser.pages();
          let newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });
          await newTab.reload({ waitUntil: "networkidle0" });
          await newTab.waitFor("//span[contains(., 'Process for pipeline exited')]", {
            timeout: 0,
          });
          const image = await newTab.screenshot({
            path: screenshotPath("/hello_cereal_figure_three.png"),
          });
          expect(image).toMatchImageSnapshot(setConfig("hello_cereal_figure_three"));
          resolve();
        } catch (error) {
          reject(error);
        }
      });
    });
    await executeButton.click();
    await done;
    return;
  });
});

describe("for the serial pipeline in hello_dag", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f serial_pipeline.py -a serial_pipeline
    dagit = await runDagit(["-f", "serial_pipeline.py", "-a", "serial_pipeline"], 3000, "basics", "e03_pipelines");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    browser.removeAllListeners("targetcreated");
    done();
  });

  it("renders the pipelines view for the serial pipeline", async () => {
    await page.goto("http://127.0.0.1:3000/pipeline/serial_pipeline/", {
      waitUntil: "networkidle0",
    });
    const image = await page.screenshot({
      path: screenshotPath("/serial_pipeline_figure_one.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("serial_pipeline_figure_one"));
    return;
  });
});

describe("for the complex pipeline in hello_dag", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f complex_pipeline.py -a complex_pipeline
    dagit = await runDagit(["-f", "complex_pipeline.py", "-a", "complex_pipeline"], 3000, "basics", "e03_pipelines");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    browser.removeAllListeners("targetcreated");
    done();
  });

  it("renders the pipelines view for the complex pipeline", async () => {
    await page.goto("http://127.0.0.1:3000/pipeline/complex_pipeline/", {
      waitUntil: "networkidle0",
    });
    await sleep(500);
    const image = await page.screenshot({
      path: screenshotPath("/complex_pipeline_figure_one.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("complex_pipeline_figure_one"));
    return;
  });
});

describe("for the config editor in inputs", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f inputs.py -a inputs_pipeline
    dagit = await runDagit(["-f", "inputs.py", "-a", "inputs_pipeline"], 3000, "basics", "e02_solids");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    await tearDownDagit(dagit);
    try {
      await browser.close();
    } catch { }
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    browser.removeAllListeners("targetcreated");
    done();
  });

  it("renders the playground view for the inputs pipeline with a hover error", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__inputs_pipeline@inputs.py:inputs_pipeline/pipelines/inputs_pipeline/playground", {
      waitUntil: "networkidle0",
    });
    await sleep(500);
    await page.waitForSelector('div[class="RunPreview__Item-sc-5v37v5-4 PySGd"]', {
      timeout: 5000,
    });
    await page.hover('div[class="RunPreview__Item-sc-5v37v5-4 PySGd"]');
    await sleep(50);
    const image = await page.screenshot({
      path: screenshotPath("/inputs_figure_one.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("inputs_figure_one"));
    return;
  });

  it("renders the playground view for the inputs pipeline with typeahead", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__inputs_pipeline@inputs.py:inputs_pipeline/pipelines/inputs_pipeline/playground", {
      waitUntil: "networkidle0",
    });
    await sleep(500);
    await page.waitForSelector(".CodeMirror textarea", { timeout: 5000 });
    await page.click(".CodeMirror textarea");
    await page.keyboard.down("Control");
    await page.keyboard.down("Space");
    await sleep(50);
    const image = await page.screenshot({
      path: screenshotPath("/inputs_figure_two.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("inputs_figure_two"));
    return;
  });

  it("renders the playground view for the inputs pipeline with valid config", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__inputs_pipeline@inputs.py:inputs_pipeline/pipelines/inputs_pipeline/playground", {
      waitUntil: "networkidle0",
    });
    await sleep(1000);
    await page.waitForSelector(".CodeMirror textarea", { timeout: 5000 });
    await page.type(
      ".CodeMirror textarea",
      "solids\n" +
      "read_csv\n" +
      "inputs\n" +
      "csv_path\n" +
      'value: "cereal.csv"'
    );
    await page.waitForSelector('button[type="button"][status="ready"]');
    const image = await page.screenshot({
      path: screenshotPath("/inputs_figure_three.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("inputs_figure_three"));
    return;
  });
});

describe("for the untyped pipeline in typed_inputs", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f inputs.py -a inputs_pipeline
    dagit = await runDagit(["-f", "inputs.py", "-a", "inputs_pipeline"], 3000, "basics", "e02_solids");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders the pipelines view for the inputs pipeline with the type annotations for a solid", async () => {
    await page.goto("http://127.0.0.1:3000/pipeline/inputs_pipeline/", {
      waitUntil: "networkidle2",
    });
    const [readCsvSolid] = await page.$x(
      "//*[name()='svg']/*[name()='g']/*[name()='text' and contains(text(), 'read_csv')]"
    );
    await readCsvSolid.click();
    await sleep(50);
    const image = await page.screenshot({
      path: screenshotPath("/inputs_figure_four.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("inputs_figure_four"));
  });

  it("renders the playground view for the inputs pipeline with a runtime error due to bad config", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__inputs_pipeline@inputs.py:inputs_pipeline/pipelines/inputs_pipeline/playground", {
      waitUntil: "networkidle2",
    });
    await sleep(500);
    await page.type(
      ".CodeMirror textarea",
      "solids\n" + "read_csv\n" + "inputs\n" + "csv_path\n" + "value: 2343"
    );
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[type="button"][status="ready"]'
    );

    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          const pages = await browser.pages();
          const newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });
          await newTab.waitFor(3000);
          const image = await newTab.screenshot({
            path: screenshotPath("/inputs_figure_five.png"),
          });
          expect(image).toMatchImageSnapshot(setConfig("inputs_figure_five"));
          resolve();
        } catch (error) {
          reject(error);
        }
      });
    });

    await executeButton.click();
    await done;
  });

  it("renders an error detail for the inputs pipeline with a runtime error due to bad config", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__inputs_pipeline@inputs.py:inputs_pipeline/pipelines/inputs_pipeline/playground", {
      waitUntil: "networkidle2",
    });
    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);
    await page.type(
      ".CodeMirror textarea",
      "solids\n" + "read_csv\n" + "inputs\n" + "csv_path\n" + "value: 2343"
    );
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[type="button"][status="ready"]'
    );

    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          console.log("awaiting pages");
          const pages = await browser.pages();
          const newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });
          await newTab.waitFor(3000);
          const [viewFullMessage] = await newTab.$x("//div[contains(text(), 'View Full Message')]");
          await viewFullMessage.click();
          await sleep(50);
          const image = await newTab.screenshot({
            path: screenshotPath("/inputs_figure_six.png"),
          });
          expect(image).toMatchImageSnapshot(setConfig("inputs_figure_six"));
          resolve();
        } catch (error) {
          reject(error);
        }
      });
    });

    await executeButton.click();
    await done;
  });
});

describe("for the typed pipeline in typed_inputs", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f inputs_typed.py -a inputs_pipeline
    dagit = await runDagit(["-f", "inputs_typed.py", "-a", "inputs_pipeline"], 3000, "basics", "e04_quality");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders the playground view for the inputs pipeline with an error due to bad config", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__inputs_pipeline@inputs_typed.py:inputs_pipeline/pipelines/inputs_pipeline/playground", {
      waitUntil: "networkidle2",
    });
    await sleep(500);
    await page.type(
      ".CodeMirror textarea",
      "solids\n" + "read_csv\n" + "inputs\n" + "csv_path:\n" + "\n  value: 2343"
    );
    await sleep(500);
    await page.waitForSelector(".CodeMirror-lint-marker-error", {
      timeout: 0,
    });
    await page.hover(".CodeMirror textarea");

    const image = await page.screenshot({
      path: screenshotPath("/inputs_figure_seven.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("inputs_figure_seven"));
  });
});

describe("for the config pipeline in config", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f config.py -a config_pipeline
    dagit = await runDagit(["-f", "config_more_details.py", "-a", "config_pipeline"], 3000, "basics", "e02_solids");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders the pipelines view for the config pipeline with the config type for a solid", async () => {
    await page.goto("http://127.0.0.1:3000/pipeline/config_pipeline/", {
      waitUntil: "networkidle2",
    });
    const [readCsvSolid] = await page.$x(
      "//*[name()='svg']/*[name()='g']/*[name()='text' and contains(text(), 'sort_by_calories')]"
    );
    await readCsvSolid.click();
    await sleep(50);
    const image = await page.screenshot({
      path: screenshotPath("/config_figure_one.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("config_figure_one"));
  });
});

describe("for the custom types pipeline in types", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f custom_types.py -a custom_type_pipeline
    dagit = await runDagit(["-f", "custom_types.py", "-a", "custom_type_pipeline"], 3000, "basics", "e04_quality");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders the pipelines view with read_csv selected", async () => {
    await page.goto("http://127.0.0.1:3000/pipeline/custom_type_pipeline/", {
      waitUntil: "networkidle2",
    });
    const [readCsvSolid] = await page.$x(
      "//*[name()='svg']/*[name()='g']/*[name()='text' and contains(text(), 'read_csv')]"
    );
    await readCsvSolid.click();
    await sleep(50);
    const image = await page.screenshot({
      path: screenshotPath("/custom_types_figure_one.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("custom_types_figure_one"));
  });
});

describe("for the custom types pipeline in metadata", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f custom_types_4.py -a custom_type_pipeline
    dagit = await runDagit(["-f", "custom_types_4.py", "-a", "custom_type_pipeline"], 3000, "basics", "e04_quality");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders a pipeline run with the sort_by_calories.compute metadata", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__custom_type_pipeline@custom_types_4.py:custom_type_pipeline/pipelines/custom_type_pipeline/playground", {
      waitUntil: "networkidle0",
    });
    await sleep(1000);
    await page.waitForSelector(".CodeMirror textarea", { timeout: 5000 });
    await page.type(
      ".CodeMirror textarea",
      "solids\n" +
      "sort_by_calories\n" +
      "inputs\n" +
      "cereals\n" +
      'csv_path: "cereal.csv"'
    );

    const executeButton = await page.waitForSelector(
      'button[type="button"][status="ready"]'
    );

    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          console.log("awaiting pages");
          const pages = await browser.pages();
          const newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });
          await newTab.waitFor(3000);

          const image = await newTab.screenshot({
            path: screenshotPath("/custom_types_figure_two.png"),
          });
          expect(image).toMatchImageSnapshot(setConfig("custom_types_figure_two"));
          resolve();
        } catch (error) {
          reject(error);
        }
      });
    });

    await executeButton.click();
    await done;
  });
});

describe("for the custom types pipeline in expectations", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f custom_types_bad_5.py -a custom_type_pipeline
    dagit = await runDagit(["-f", "custom_types_bad_5.py", "-a", "custom_type_pipeline"], 3000, "basics", "e04_quality");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders a pipeline run with the sort_by_calories.compute expectation result", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__custom_type_pipeline@custom_types_bad_5.py:custom_type_pipeline/pipelines/custom_type_pipeline/playground", {
      waitUntil: "networkidle0",
    });
    
    await page.waitForSelector(".CodeMirror textarea", { timeout: 5000 });
    await page.type(
      ".CodeMirror textarea",
      "solids\n" +
      "sort_by_calories\n" +
      "inputs\n" +
      "cereals\n" +
      'csv_path: "cereal.csv"'
    );

    const executeButton = await page.waitForSelector(
      'button[type="button"][status="ready"]'
    );

    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          console.log("awaiting pages");
          const pages = await browser.pages();
          const newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });
          await newTab.waitForSelector('div[title="for-screenshots"]', { timeout: 0 });
          
          const image = await newTab.screenshot({
            path: screenshotPath("/custom_types_bad_data.png"),
          });
          expect(image).toMatchImageSnapshot(setConfig("custom_types_bad_data"));
          resolve();
        } catch (error) {
          reject(error);
        }
      });
    });

    await executeButton.click();
    await done;
  });
});

describe("for the multiple outputs pipeline in multiple_outputs", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f multiple_outputs.py -a multiple_outputs_pipeline
    dagit = await runDagit(["-f", "multiple_outputs.py", "-a", "multiple_outputs_pipeline"], 3000, "basics", "e02_solids");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders the pipeline view for the multiple outputs pipeline", async () => {
    await page.goto("http://127.0.0.1:3000/pipeline/multiple_outputs_pipeline/", {
      waitUntil: "networkidle0",
    });
    await sleep(500);
    const image = await page.screenshot({
      path: screenshotPath("/multiple_outputs.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("multiple_outputs"));
    return;
  });

  it("renders the pipelines view with split_cereals selected", async () => {
    await page.goto("http://127.0.0.1:3000/pipeline/multiple_outputs_pipeline/", {
      waitUntil: "networkidle0",
    });

    const [zoomInButton] = await page.$x("//*[name()='svg'][@data-icon='zoom-in']");
    await zoomInButton.click();
    await sleep(50);

    const [splitCerealsSolid] = await page.$x(
      "//*[name()='svg']/*[name()='g']/*[name()='text' and contains(text(), 'split_cereals')]"
    );
    await splitCerealsSolid.click();
    await sleep(50);
    const image = await page.screenshot({
      path: screenshotPath("/multiple_outputs_zoom.png"),
    });
    expect(image).toMatchImageSnapshot({
      // This is not ideal, but this test is a little flakier (due to positioning issues in zoom?)
      failureThreshold: "0.02",
      failureThresholdType: "percent",
      customSnapshotIdentifier: "multiple_outputs_zoom",
      customSnapshotsDir: "__generated__/",
      customDiffDir: "__generated__/",
    });
  });

  it("renders execution results with cold cereal processing disabled", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__multiple_outputs_pipeline@multiple_outputs.py:multiple_outputs_pipeline/pipelines/multiple_outputs_pipeline/playground", {
      waitUntil: "networkidle0",
    });

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);
    await page.type(
      ".CodeMirror textarea",
      "solids\n" + "read_csv\n" + "inputs\n" + "csv_path\n" + 'value: "cereal.csv"\n'
    );
    await page.focus(".CodeMirror textarea");
    for (let i = 0; i < 4; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(
      ".CodeMirror textarea",
      "  split_cereals\n" + "  config:\n" + "  process_hot: true\n" + "process_cold: false"
    );
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[type="button"][status="ready"]'
    );
    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          console.log("awaiting pages");
          const pages = await browser.pages();
          const newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });
          await newTab.waitFor(3000);
          const image = await newTab.screenshot({
            path: screenshotPath("/conditional_outputs.png"),
          });
          expect(image).toMatchImageSnapshot(setConfig("conditional_outputs"));
          resolve();
        } catch (error) {
          reject(error);
        }
      });
    });

    await executeButton.click();
    await done;
  });
});

describe("for the multiple outputs pipeline in reusable", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f reusable_solids.py -a reusable_solids_pipeline
    dagit = await runDagit(["-f", "reusable_solids.py", "-a", "reusable_solids_pipeline"], 3000, "advanced", "solids");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders the pipeline view for the reusable pipeline with sort_hot_cereals highlighted", async () => {
    await page.goto("http://127.0.0.1:3000/pipeline/reusable_solids_pipeline/", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    const [zoomInButton] = await page.$x("//*[name()='svg'][@data-icon='zoom-in']");
    await zoomInButton.click();
    await sleep(50);

    const [sortHotCerealsSolid] = await page.$x(
      "//*[name()='svg']/*[name()='g']/*[name()='text' and contains(text(), 'sort_hot_cereals')]"
    );
    await sortHotCerealsSolid.click();
    await sleep(50);
    const image = await page.screenshot({
      path: screenshotPath("/reusable_solids.png"),
    });
    expect(image).toMatchImageSnapshot({
      // This is not ideal, but this test is a little flakier (due to positioning issues in zoom?)
      failureThreshold: "0.021",
      failureThresholdType: "percent",
      customSnapshotIdentifier: "reusable_solids",
      customSnapshotsDir: "__generated__/",
      customDiffDir: "__generated__/",
    });
  });
});

describe("for the composition pipeline in composite_solids", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f composite_solids.py -a composite_solids_pipeline
    dagit = await runDagit(["-f", "composite_solids.py", "-a", "composite_solids_pipeline"], 3000, "advanced", "solids");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders the pipeline view for the composite solids pipeline with load_cereals highlighted", async () => {
    await page.goto("http://127.0.0.1:3000/pipeline/composite_solids_pipeline/", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    const [zoomInButton] = await page.$x("//*[name()='svg'][@data-icon='zoom-in']");
    await zoomInButton.click();
    const [loadCerealsSolid] = await page.$x(
      "//*[name()='svg']/*[name()='g']/*[name()='text' and contains(text(), 'load_cereals')]"
    );
    await loadCerealsSolid.click();

    const image = await page.screenshot({
      path: screenshotPath("/composite_solids.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("composite_solids"));
  });

  it("renders the pipeline view for the composite solids pipeline with load_cereals expanded", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__composite_solids_pipeline@composite_solids.py:composite_solids_pipeline/pipelines/composite_solids_pipeline/load_cereals", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    const [expand] = await page.$x("//*[name()='rect'][@height='32'][@width='105.28']");
    await expand.click();
    await sleep(2000);
    const [zoomInButton] = await page.$x("//*[name()='svg'][@data-icon='zoom-in']");
    await zoomInButton.click();

    const image = await page.screenshot({
      path: screenshotPath("/composite_solids_expanded.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("composite_solids_expanded"));
  });

  it("renders execution results for the composite solids pipeline", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__composite_solids_pipeline@composite_solids.py:composite_solids_pipeline/pipelines/composite_solids_pipeline/playground", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids\n" +
      "load_cereals\n" +
      "solids\n" +
      "read_cereals\n" +
      "inputs\n" +
      "csv_path:\n\n" +
      '  value: "cereal.csv"\n'
    );
    await page.focus(".CodeMirror textarea");
    for (let i = 0; i < 3; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(
      ".CodeMirror textarea",
      "read_manufacturers\n" +
      "config\n" +
      'delimiter: ";"\n'
    );
    await page.type(".CodeMirror textarea", "\n");
    await page.keyboard.press("Backspace");
    await page.type(
      ".CodeMirror textarea",
      "inputs:\n" + "  csv_path:\n" + '  value: "manufacturers.csv"\n'
    );
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[type="button"][status="ready"]'
    );
    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          console.log("awaiting pages");
          const pages = await browser.pages();
          const newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });
          await newTab.waitFor(3000);
          const image = await newTab.screenshot({
            path: screenshotPath("/composite_solids_results.png"),
          });
          expect(image).toMatchImageSnapshot(setConfig("composite_solids_results"));
          resolve();
        } catch (error) {
          reject(error);
        }
      });
    });

    await executeButton.click();
    await done;
  });
});

describe("for the materialization pipeline in materializations", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f materializations.py -a materialization_pipeline
    dagit = await runDagit(["-f", "materializations.py", "-a", "materialization_pipeline"], 3000, "advanced", "materializations");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });
  
  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders execution results for the materializations pipeline", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__materialization_pipeline@materializations.py:materialization_pipeline/pipelines/materialization_pipeline/playground", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids\n" + "read_csv\n" + "inputs\n" + "csv_path\n" + 'value: "cereal.csv"\n'
    );
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[type="button"][status="ready"]'
    );
    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          console.log("awaiting pages");
          const pages = await browser.pages();
          const newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });
          await newTab.waitFor(3000);
          const image = await newTab.screenshot({
            path: screenshotPath("/materializations.png"),
          });
          expect(image).toMatchImageSnapshot(setConfig("materializations"));
          resolve();
        } catch (error) {
          reject(error);
        }
      });
    });

    await executeButton.click();
    await done;
  });

  it("renders execution results for the materializations pipeline with intermediates enabled", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__materialization_pipeline@materializations.py:materialization_pipeline/pipelines/materialization_pipeline/playground", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids\n" + "read_csv\n" + "inputs\n" + "csv_path\n" + 'value: "cereal.csv"\n'
    );
    await page.focus(".CodeMirror textarea");
    for (let i = 0; i < 4; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(".CodeMirror textarea", "storage\n" + "filesystem\n");
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[type="button"][status="ready"]'
    );
    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          console.log("awaiting pages");
          const pages = await browser.pages();
          const newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });
          await newTab.waitFor(3000);
          const image = await newTab.screenshot({
            path: screenshotPath("/intermediates.png"),
          });
          expect(image).toMatchImageSnapshot(setConfig("intermediates"));
          resolve();
        } catch (error) {
          reject(error);
        }
      });
    });

    await executeButton.click();
    await done;
  });
});

describe("for the reexecution pipeline in intermediates", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f reexecution.py -a reexecution_pipeline
    dagit = await runDagit(["-f", "reexecution.py", "-a", "reexecution_pipeline"], 3000, "advanced", "intermediates");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders the highlighted selected step subset for the reexecution pipeline with the Re-execute(sort_by_calories.compute) button", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__reexecution_pipeline@reexecution.py:reexecution_pipeline/pipelines/reexecution_pipeline/playground", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids\n" + "read_csv\n" + "inputs\n" + "csv_path:\n" // we put two \n because there's a delay for dagit to pick up config yaml
    );
    await page.type(
      ".CodeMirror textarea", '\n  value: "cereal.csv"\n'
    );
    await page.focus(".CodeMirror textarea");
    for (let i = 0; i < 4; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(".CodeMirror textarea", "storage\n" + "filesystem:");
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[type="button"][status="ready"]'
    );
    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          console.log("awaiting pages");
          const pages = await browser.pages();
          const newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });
          await newTab.waitFor(3000);

          await page.$x('//div[@title="sort_by_calories.compute"]');
          const [substep] = await newTab.$x(
            '//div//div[text()="sort_by_calories.compute"]'
          );
          await substep.click();

          const image = await newTab.screenshot({
            path: screenshotPath("/reexecution.png"),
          });
          expect(image).toMatchImageSnapshot(setConfig("reexecution"));
          resolve();
        } catch (error) {
          reject(error);
        }
      });
    });

    await executeButton.click();
    await done;
  });

  it("renders reexecution results for the reexecution pipeline", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__reexecution_pipeline@reexecution.py:reexecution_pipeline/pipelines/reexecution_pipeline/playground", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids\n" + "read_csv\n" + "inputs\n" + "csv_path:\n" + '\n  value: "../../cereal.csv"\n'
    );
    await page.focus(".CodeMirror textarea");
    for (let i = 0; i < 4; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(".CodeMirror textarea", "storage\n" + "filesystem:");
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[type="button"][status="ready"]'
    );
    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          console.log("awaiting pages");
          const pages = await browser.pages();
          const newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });
          await newTab.waitFor(3000);

          const [substep] = await newTab.$x(
            '//div//div[text()="sort_by_calories.compute"]'
          );
          await substep.click();
          await sleep(50);

          browser.removeAllListeners("targetcreated");

          const [reexecuteReadCsvButton] = await newTab.$x(
            '//button//span[text()="Re-execute (sort_by_calories.compute)"]'
          );
          await reexecuteReadCsvButton.click();
          await newTab.waitFor(5000);
          const image = await newTab.screenshot({
            path: screenshotPath("/reexecution_results.png"),
          });
          expect(image).toMatchImageSnapshot(setConfig("reexecution_results"));
          resolve();
          return await reallyDone;
        } catch (error) {
          reject(error);
        }
      });
    });

    await executeButton.click();
    await done;
  });

  it("renders the config editor error for the reexecution pipeline with pickle input but no subset", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__reexecution_pipeline@reexecution.py:reexecution_pipeline/pipelines/reexecution_pipeline/playground", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids\n" +
      "sort_by_calories\n" +
      "inputs:\n" +
      "  cereals:\n" +
      "  pickle:\n" +
      '  path: "/dagster_home/storage/2584d954-a30f-4be6-bbfc-c919e4bee84b/intermediates/read_csv.compute/result"'
    );
    await page.type(
      ".CodeMirror textarea", "\n"
    );
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(".CodeMirror textarea", "storage\n" + "filesystem\n");
    await page.evaluate(() => {
      document.querySelector(".CodeMirror-scroll").scrollBy(-50, 0);
    });
    await sleep(5000);

    await page.waitForSelector(".CodeMirror-lint-mark-error");
    const image = await page.screenshot({
      path: screenshotPath("/reexecution_errors.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("reexecution_errors"));
    return;
  });

  it("renders the subset selector for the reexecution pipeline with pickle input", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__reexecution_pipeline@reexecution.py:reexecution_pipeline/pipelines/reexecution_pipeline/playground", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids\n" +
      "sort_by_calories\n" +
      "inputs:\n" +
      "  cereals:\n" +
      "  - pickle:" +
      '\n    path: "/dagster_home/storage/2584d954-a30f-4be6-bbfc-c919e4bee84b/intermediates/read_csv.compute/result"'
    );

    await page.waitForSelector(".CodeMirror-lint-mark-error");
    await page.click("input[title=graph-query-input]");
    await sleep(100);
    await page.keyboard.press("Backspace");
    await page.type("input[title=graph-query-input]", "sort_by_calories\n"); // before hitting "enter", the config error won't disappear
    await page.click("input[title=graph-query-input]");
    await page.waitForSelector('button[status="ready"]');
    const image = await page.screenshot({
      path: screenshotPath("/subset_selection.png"), 
    });
    expect(image).toMatchImageSnapshot(setConfig("subset_selection"));
    return;
  });
});

describe("for the output materialization pipeline in materializations", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f output_materialization.py -a output_materialization_pipeline
    dagit = await runDagit(
      ["-f", "output_materialization.py", "-a", "output_materialization_pipeline"],
      3000,
      "advanced",
      "materializations"
    );
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders execution results for the output materialization pipeline", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__output_materialization_pipeline@output_materialization.py:output_materialization_pipeline/pipelines/output_materialization_pipeline/playground", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids\n" +
      "sort_by_calories\n" +
      "inputs\n" +
      "cereals\n" +
      'csv_path: "cereal.csv"\n'
    );
    await page.focus(".CodeMirror textarea");
    for (let i = 0; i < 2; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(
      ".CodeMirror textarea",
      "outputs\n" +
      "- result:\n" +
      "    csv:\n" +
      '  path: "output/cereal_out.csv"\n' +
      'sep: ";"\n'
    );
    await page.focus(".CodeMirror textarea");
    await page.keyboard.press("Backspace");
    await page.type(
      ".CodeMirror textarea",
      "json:\n" +
      '  path: "output/cereal_out.json"'
    );
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[type="button"][status="ready"]'
    );
    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          console.log("awaiting pages");
          const pages = await browser.pages();
          const newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });
          await newTab.waitFor(3000);
          const image = await newTab.screenshot({
            path: screenshotPath("/output_materializations.png"),
          });
          expect(image).toMatchImageSnapshot(setConfig("output_materializations"));
          resolve();
        } catch (error) {
          reject(error);
        }
      });
    });

    await executeButton.click();
    await done;
  });
});

describe("for the serialization strategy pipeline in intermediates", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f serialization_strategy.py -a serialization_strategy_pipeline
    dagit = await runDagit(
      ["-f", "serialization_strategy.py", "-a", "serialization_strategy_pipeline"],
      3000,
      "advanced",
      "intermediates"
    );
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders execution results for the serialization strategy pipeline", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__serialization_strategy_pipeline@serialization_strategy.py:serialization_strategy_pipeline/pipelines/serialization_strategy_pipeline/playground", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids\n" + "read_csv\n" + "inputs\n" + "csv_path:\n" + '\n  value: "cereal.csv"\n'
    );
    await page.focus(".CodeMirror textarea");
    for (let i = 0; i < 4; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(".CodeMirror textarea", "storage\n" + "filesystem:");
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[type="button"][status="ready"]'
    );
    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          console.log("awaiting pages");
          const pages = await browser.pages();
          const newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });
          await newTab.waitFor(3000);
          const image = await newTab.screenshot({
            path: screenshotPath("/serialization_strategy.png"),
          });
          expect(image).toMatchImageSnapshot(setConfig("serialization_strategy"));
          resolve();
        } catch (error) {
          reject(error);
        }
      });
    });

    await executeButton.click();
    await done;
  });
});

describe("for the modes pipeline in modes", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f modes.py -a modes_pipeline
    dagit = await runDagit(["-f", "modes.py", "-a", "modes_pipeline"], 3000, "advanced", "pipelines");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders the mode selector for the modes pipeline", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__modes_pipeline@modes.py:modes_pipeline/pipelines/modes_pipeline/playground", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids\n" +
      "read_csv\n" +
      "inputs\n" +
      "csv_path\n" +
      'value: "cereal.csv"\n'
    );
    for (let i = 0; i < 4; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(
      ".CodeMirror textarea",
      "resources\n" +
      "warehouse\n" +
      "config\n" +
      'conn_str: ":memory:"'
    );
    await page.waitForSelector(
            'button[type="button"][status="ready"]'
          );
    await page.click("button[data-test-id='mode-picker-button']");
    await sleep(500);

    const image = await page.screenshot({
      path: screenshotPath("/modes.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("modes"));
  });
});

describe("for the presets pipeline in presets", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f presets.py -a presets_pipeline
    dagit = await runDagit(["-f", "presets.py", "-a", "presets_pipeline"], 3000, "advanced", "pipelines"
    );
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders the presets selector for the presets pipeline", async () => {
    await page.goto("http://localhost:3000/workspace/__repository__presets_pipeline@presets.py:presets_pipeline/pipelines/presets_pipeline/playground", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids\n" + 
      "read_csv\n" + 
      "inputs\n" + 
      "csv_path\n" + 
      'value: "cereal.csv"\n'
    );
    for (let i = 0; i < 4; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(
      ".CodeMirror textarea",
      "resources\n" + 
      "warehouse\n" +
      "config\n" +
      'conn_str: "postgres://test:test@localhost:5432/test"'
    );
    await page.waitForSelector(
            'button[type="button"][status="ready"]'
          );

    await page.click("button[data-test-id='mode-picker-button']");
    await sleep(50);
    const [devModeItem] = await page.$x('//li//a//div[contains(text(), "dev")]');
    await devModeItem.click();
    await sleep(50);

    await page.click("button[data-test-id='preset-selector-button']");
    await sleep(50);
    const [devPresetItem] = await page.$x('//li//a//div[contains(text(), "dev")]');
    await devPresetItem.click();
    await sleep(50);

    await page.click("button[data-test-id='preset-selector-button']");
    await sleep(50);

    const image = await page.screenshot({
      path: screenshotPath("/presets.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("presets"));
  });
});

describe("for the repo", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f repos.py
    dagit = await runDagit(["-f", "repos.py"], 3000, "advanced", "repositories");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders the pipeline selector ", async () => {
    await page.goto("http://127.0.0.1:3000/pipeline/complex_pipeline/", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.click('input[type="text"][placeholder="Search pipelines..."]');
    await sleep(50);

    const image = await page.screenshot({
      path: screenshotPath("/repos.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("repos"));
  });
});

describe("for the scheduling", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f scheduler.py
    dagit = await runDagit(["-f", "scheduler.py"], 3000, "advanced", "scheduling");
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch { }
    await tearDownDagit(dagit);
    done();
  });

  beforeEach(async (done) => {
    let existingPage;
    for (existingPage of await browser.pages()) {
      await existingPage.close();
    }
    browser.removeAllListeners("targetcreated");
    page = await browser.newPage();
    await page.setViewport({ width: 1680, height: 946 });
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    done();
  });

  it("renders the pipeline with Schedules section ", async () => {
    await page.goto("http://127.0.0.1:3000/pipeline/hello_cereal_pipeline/", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    const image = await page.screenshot({
      path: screenshotPath("/schedules.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("schedules"));
  });

  it("renders the pipeline with scheduled runs ", async () => {
    await page.goto("http://127.0.0.1:3000/pipeline/hello_cereal_pipeline/", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    const [goodMorningSchedule] = await page.$x('//div[@class="SchedulesList__Label-iq7kk9-1 lojUag"]');
    await goodMorningSchedule.click();
    await page.waitForSelector(".bp3-switch-inner-text");

    const image = await page.screenshot({
      path: screenshotPath("/good_morning_schedule.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("good_morning_schedule"));
  });
});