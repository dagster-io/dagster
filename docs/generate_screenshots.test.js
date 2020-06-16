const puppeteer = require("puppeteer");
const { toMatchImageSnapshot } = require("jest-image-snapshot");
const { spawn } = require("child_process");
const sleep = require("system-sleep");

expect.extend({ toMatchImageSnapshot });

const screenshotPath = (pathFragment) =>
  __dirname + "/next/public/assets/images/tutorial/" + pathFragment;

const runDagit = async (args, port) => {
  const dagitArgs = args.concat(["-p", port || 3000]);

  dagit = spawn("dagit", dagitArgs, {
    cwd: "../examples/dagster_examples/intro_tutorial/",
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
  console.log(`stopped dagit`);
  await sleep(5000);
  return;
};

setConfig = (filename) => ({
  failureThreshold: "0.01",
  failureThresholdType: "percent",
  customSnapshotIdentifier: filename,
});

describe("for hello_solid, hello_pipeline, and execute_pipeline", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f hello_cereal.py -n hello_cereal_pipeline
    dagit = await runDagit(
      ["-f", "hello_cereal.py", "-a", "hello_cereal_pipeline"],
      3000
    );
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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
    await page.goto("http://127.0.0.1:3000/pipeline/hello_cereal_pipeline:/", {
      waitUntil: "networkidle2",
    });
    const image = await page.screenshot({
      path: screenshotPath("/hello_cereal_figure_one.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("hello_cereal_figure_one"));
    return;
  });

  it("renders the playground for the hello cereal pipeline", async () => {
    await page.goto("http://127.0.0.1:3000/playground/hello_cereal_pipeline", {
      waitUntil: "networkidle2",
    });

    const image = await page.screenshot({
      path: screenshotPath("/hello_cereal_figure_two.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("hello_cereal_figure_two"));
    return;
  });

  it("renders the executed playground view for the hello cereal pipeline", async () => {
    await page.goto("http://127.0.0.1:3000/playground/hello_cereal_pipeline", {
      waitUntil: "networkidle2",
    });

    const executeButton = await page.waitForSelector(
      'button[title="Start execution in a subprocess"]'
    );

    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          const pages = await browser.pages();
          let newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });

          await newTab.reload({ waitUntil: "networkidle0" });
          await newTab.waitFor(
            "//span[contains(., 'Process for pipeline exited')]",
            { timeout: 0 }
          );
          const image = await newTab.screenshot({
            path: screenshotPath("/hello_cereal_figure_three.png"),
          });
          expect(image).toMatchImageSnapshot(
            setConfig("hello_cereal_figure_three")
          );
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
    // dagit -f serial_pipeline.py -n serial_pipeline
    dagit = await runDagit(
      ["-f", "serial_pipeline.py", "-a", "serial_pipeline"],
      3000
    );
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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
    // dagit -f complex_pipeline.py -n complex_pipeline
    dagit = await runDagit(
      ["-f", "complex_pipeline.py", "-a", "complex_pipeline"],
      3000
    );
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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
    expect(image).toMatchImageSnapshot(
      setConfig("complex_pipeline_figure_one")
    );
    return;
  });
});

describe("for the config editor in inputs", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f inputs.py -n inputs_pipeline
    dagit = await runDagit(["-f", "inputs.py", "-a", "inputs_pipeline"], 3000);
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    await tearDownDagit(dagit);
    try {
      await browser.close();
    } catch {}
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
    await page.goto("http://127.0.0.1:3000/playground/inputs_pipeline/", {
      waitUntil: "networkidle0",
    });
    await sleep(500);
    await page.waitForSelector(".CodeMirror-lint-marker-error", {
      timeout: 0,
    });
    await page.hover(".CodeMirror-lint-marker-error");
    await sleep(50);
    const image = await page.screenshot({
      path: screenshotPath("/inputs_figure_one.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("inputs_figure_one"));
    return;
  });

  it("renders the playground view for the inputs pipeline with typeahead", async () => {
    await page.goto("http://127.0.0.1:3000/playground/inputs_pipeline/", {
      waitUntil: "networkidle0",
    });
    await sleep(500);
    await page.waitForSelector(".CodeMirror textarea", { timeout: 0 });
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
    await page.goto("http://127.0.0.1:3000/playground/inputs_pipeline/", {
      waitUntil: "networkidle0",
    });
    await sleep(1000);
    await page.waitForSelector(".CodeMirror textarea", { timeout: 0 });
    await page.type(
      ".CodeMirror textarea",
      "solids:\n" +
        "  read_csv:\n" +
        "  inputs:\n" +
        "    csv_path:\n" +
        '      value: "cereal.csv"'
    );
    await page.waitForSelector(
      'button[title="Start execution in a subprocess"]'
    );
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
    // dagit -f inputs.py -n inputs_pipeline
    dagit = await runDagit(["-f", "inputs.py", "-a", "inputs_pipeline"], 3000);
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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
    await page.goto("http://127.0.0.1:3000/playground/inputs_pipeline/", {
      waitUntil: "networkidle2",
    });
    await sleep(500);
    await page.type(
      ".CodeMirror textarea",
      "solids:\n" +
        "  read_csv:\n" +
        "  inputs:\n" +
        "  csv_path:\n" +
        "  value: 2343"
    );
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[title="Start execution in a subprocess"]'
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
    await page.goto("http://127.0.0.1:3000/playground/inputs_pipeline/", {
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
      "solids:\n" +
        "  read_csv:\n" +
        "  inputs:\n" +
        "  csv_path:\n" +
        "  value: 2343"
    );
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[title="Start execution in a subprocess"]'
    );

    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          console.log("awaiting pages");
          const pages = await browser.pages();
          const newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });
          await newTab.waitFor(3000);
          const [viewFullMessage] = await newTab.$x(
            "//div[contains(text(), 'View Full Message')]"
          );
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
    // dagit -f inputs_typed.py -n inputs_pipeline
    dagit = await runDagit(
      ["-f", "inputs_typed.py", "-a", "inputs_pipeline"],
      3000
    );
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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
    await page.goto("http://127.0.0.1:3000/playground/inputs_pipeline/", {
      waitUntil: "networkidle2",
    });
    await sleep(500);
    await page.type(
      ".CodeMirror textarea",
      "solids:\n" +
        "  read_csv:\n" +
        "  inputs:\n" +
        "  csv_path:\n" +
        "  value: 2343"
    );
    await sleep(500);
    await page.waitForSelector(".CodeMirror-lint-marker-error", {
      timeout: 0,
    });
    await page.hover(".CodeMirror-lint-marker-error");
    await sleep(50);
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
    // dagit -f config.py -n config_pipeline
    dagit = await runDagit(["-f", "config.py", "-a", "config_pipeline"], 3000);
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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

  it("renders the playground view with the mini schema", async () => {
    await page.goto("http://127.0.0.1:3000/playground/config_pipeline/", {
      waitUntil: "networkidle2",
    });
    await sleep(500);
    await page.type(
      ".CodeMirror textarea",
      "solids:\n" +
        "  read_csv:\n" +
        "  inputs:\n" +
        "  csv_path:\n" +
        "  value: 2343\n"
    );
    await page.focus(".CodeMirror textarea");
    for (let i = 0; i < 4; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(
      ".CodeMirror textarea",
      "    config:\n" + '  delimiter: ";"'
    );
    await sleep(500);
    const image = await page.screenshot({
      path: screenshotPath("/config_figure_one.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("config_figure_one"));
  });

  it("renders the pipelines view for the config pipeline with the config type for a solid", async () => {
    await page.goto("http://127.0.0.1:3000/pipeline/config_pipeline/", {
      waitUntil: "networkidle2",
    });
    const [readCsvSolid] = await page.$x(
      "//*[name()='svg']/*[name()='g']/*[name()='text' and contains(text(), 'read_csv')]"
    );
    await readCsvSolid.click();
    await sleep(50);
    const image = await page.screenshot({
      path: screenshotPath("/config_figure_two.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("config_figure_two"));
  });
});

describe("for the custom types pipeline in types", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f custom_types.py -n custom_type_pipeline
    dagit = await runDagit(
      ["-f", "custom_types.py", "-a", "custom_type_pipeline"],
      3000
    );
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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
    // dagit -f custom_types.py -n custom_type_pipeline
    dagit = await runDagit(
      ["-f", "custom_types_4.py", "-a", "custom_type_pipeline"],
      3000
    );
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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
    await page.goto("http://127.0.0.1:3000/playground/custom_type_pipeline/", {
      waitUntil: "networkidle0",
    });
    await sleep(1000);
    await page.waitForSelector(".CodeMirror textarea", { timeout: 0 });
    await page.type(
      ".CodeMirror textarea",
      "solids:\n" +
        "  sort_by_calories:\n" +
        "  inputs:\n" +
        "  cereals:\n" +
        '  csv: "cereal.csv"\n'
    );

    const executeButton = await page.waitForSelector(
      'button[title="Start execution in a subprocess"]'
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
          expect(image).toMatchImageSnapshot(
            setConfig("custom_types_figure_two")
          );
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
    // dagit -f custom_types.py -n custom_type_pipeline
    dagit = await runDagit(
      ["-f", "multiple_outputs.py", "-a", "multiple_outputs_pipeline"],
      3000
    );
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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
    await page.goto(
      "http://127.0.0.1:3000/pipeline/multiple_outputs_pipeline/",
      {
        waitUntil: "networkidle0",
      }
    );
    await sleep(500);
    const image = await page.screenshot({
      path: screenshotPath("/multiple_outputs.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("multiple_outputs"));
    return;
  });

  it("renders the pipelines view with split_cereals selected", async () => {
    await page.goto(
      "http://127.0.0.1:3000/pipeline/multiple_outputs_pipeline/",
      {
        waitUntil: "networkidle0",
      }
    );

    const [zoomInButton] = await page.$x(
      "//*[name()='svg'][@data-icon='zoom-in']"
    );
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
    });
  });

  it("renders execution results with cold cereal processing disabled", async () => {
    await page.goto(
      "http://127.0.0.1:3000/playground/multiple_outputs_pipeline/",
      {
        waitUntil: "networkidle0",
      }
    );

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);
    await page.type(
      ".CodeMirror textarea",
      "solids:\n" +
        "  read_csv:\n" +
        "  inputs:\n" +
        "  csv_path:\n" +
        '  value: "cereal.csv"\n'
    );
    await page.focus(".CodeMirror textarea");
    for (let i = 0; i < 4; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(
      ".CodeMirror textarea",
      "  split_cereals:\n" +
        "  config:\n" +
        "  process_hot: true\n" +
        "process_cold: false"
    );
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[title="Start execution in a subprocess"]'
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
    // dagit -f reusable_solids.py -n reusable_solids_pipeline
    dagit = await runDagit(
      ["-f", "reusable_solids.py", "-a", "reusable_solids_pipeline"],
      3000
    );
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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
    await page.goto(
      "http://127.0.0.1:3000/pipeline/reusable_solids_pipeline/",
      {
        waitUntil: "networkidle0",
      }
    );
    await sleep(500);

    const [zoomInButton] = await page.$x(
      "//*[name()='svg'][@data-icon='zoom-in']"
    );
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
    });
  });
});

describe("for the composition pipeline in composite_solids", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f composite_solids.py -n composite_solids_pipeline
    dagit = await runDagit(
      ["-f", "composite_solids.py", "-a", "composite_solids_pipeline"],
      3000
    );
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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
    await page.goto(
      "http://127.0.0.1:3000/pipeline/composite_solids_pipeline/",
      {
        waitUntil: "networkidle0",
      }
    );
    await sleep(500);

    const [zoomInButton] = await page.$x(
      "//*[name()='svg'][@data-icon='zoom-in']"
    );
    await zoomInButton.click();
    await sleep(50);

    const [loadCerealsSolid] = await page.$x(
      "//*[name()='svg']/*[name()='g']/*[name()='text' and contains(text(), 'load_cereals')]"
    );
    await loadCerealsSolid.click();
    await sleep(50);
    const image = await page.screenshot({
      path: screenshotPath("/composite_solids.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("composite_solids"));
  });

  it("renders the pipeline view for the composite solids pipeline with load_cereals expanded", async () => {
    await page.goto(
      "http://127.0.0.1:3000/pipeline/composite_solids_pipeline:/load_cereals/",
      {
        waitUntil: "networkidle0",
      }
    );
    await sleep(500);

    const [zoomInButton] = await page.$x(
      "//*[name()='svg'][@data-icon='zoom-in']"
    );
    await zoomInButton.click();
    await sleep(50);

    const image = await page.screenshot({
      path: screenshotPath("/composite_solids_expanded.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("composite_solids_expanded"));
  });

  it("renders execution results for the composite solids pipeline", async () => {
    await page.goto(
      "http://127.0.0.1:3000/playground/composite_solids_pipeline/",
      {
        waitUntil: "networkidle0",
      }
    );
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);
    // solids:
    //   load_cereals:
    //     solids:
    //       read_cereals:
    //         inputs:
    //           csv_path:
    //             value: "cereal.csv"
    //       read_manufacturers:
    //         config:
    //           delimiter: ";"
    //         inputs:
    //           csv_path:
    //             value: "manufacturers.csv"
    await page.type(
      ".CodeMirror textarea",
      "solids:\n" +
        "  load_cereals:\n" +
        "  solids:\n" +
        "  read_cereals:\n" +
        "  inputs:\n" +
        "  csv_path:\n" +
        '  value: "cereal.csv"\n'
    );
    await page.focus(".CodeMirror textarea");
    for (let i = 0; i < 3; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(
      ".CodeMirror textarea",
      "read_manufacturers:\n" + "  config:\n" + '  delimiter: ";"\n'
    );
    await page.focus(".CodeMirror textarea");
    for (let i = 0; i < 1; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(
      ".CodeMirror textarea",
      "inputs:\n" + "  csv_path:\n" + '  value: "manufacturers.csv"\n'
    );
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[title="Start execution in a subprocess"]'
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
          expect(image).toMatchImageSnapshot(
            setConfig("composite_solids_results")
          );
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

describe("for the materialization pipeline in materializations and intermediates", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f materializations.py -n materialization_pipeline
    dagit = await runDagit(
      ["-f", "materializations.py", "-a", "materialization_pipeline"],
      3000
    );
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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
    await page.goto(
      "http://127.0.0.1:3000/playground/materialization_pipeline/",
      {
        waitUntil: "networkidle0",
      }
    );
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids:\n" +
        "  read_csv:\n" +
        "  inputs:\n" +
        "  csv_path:\n" +
        '  value: "cereal.csv"\n'
    );
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[title="Start execution in a subprocess"]'
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
    await page.goto(
      "http://127.0.0.1:3000/playground/materialization_pipeline/",
      {
        waitUntil: "networkidle0",
      }
    );
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids:\n" +
        "  read_csv:\n" +
        "  inputs:\n" +
        "  csv_path:\n" +
        '  value: "cereal.csv"\n'
    );
    await page.focus(".CodeMirror textarea");
    for (let i = 0; i < 4; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(".CodeMirror textarea", "storage:\n" + "  filesystem:\n");
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[title="Start execution in a subprocess"]'
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

  it("renders execution results for the materializations pipeline with reexecution (intermediates enabled)", async () => {
    await page.goto(
      "http://127.0.0.1:3000/playground/materialization_pipeline/",
      {
        waitUntil: "networkidle0",
      }
    );
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids:\n" +
        "  read_csv:\n" +
        "  inputs:\n" +
        "  csv_path:\n" +
        '  value: "cereal.csv"\n'
    );
    await page.focus(".CodeMirror textarea");
    for (let i = 0; i < 4; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(".CodeMirror textarea", "storage:\n" + "  filesystem:\n");
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[title="Start execution in a subprocess"]'
    );
    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          console.log("awaiting pages");
          const pages = await browser.pages();
          const newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });
          await newTab.waitFor(3000);

          await page.$x('//div[@title="read_csv.compute"]');

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

  it("renders reexecution results for the materializations pipeline", async () => {
    await page.goto(
      "http://127.0.0.1:3000/playground/materialization_pipeline/",
      {
        waitUntil: "networkidle0",
      }
    );
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids:\n" +
        "  read_csv:\n" +
        "  inputs:\n" +
        "  csv_path:\n" +
        '  value: "cereal.csv"\n'
    );
    await page.focus(".CodeMirror textarea");
    for (let i = 0; i < 4; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(".CodeMirror textarea", "storage:\n" + "  filesystem:\n");
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[title="Start execution in a subprocess"]'
    );
    let done = new Promise((resolve, reject) => {
      browser.on("targetcreated", async () => {
        try {
          console.log("awaiting pages");
          const pages = await browser.pages();
          const newTab = pages[pages.length - 1];
          await newTab.setViewport({ width: 1680, height: 946 });
          await newTab.waitFor(3000);

          await newTab.evaluate(() => {
            document.querySelector('div[title="read_csv.compute"]').click();
          });
          await sleep(50);

          browser.removeAllListeners("targetcreated");

          const [reexecuteReadCsvButton] = await newTab.$x(
            '//button//span[text()="Re-execute read_csv"]'
          );

          await reexecuteReadCsvButton.click();
          await newTab.waitFor(3000);
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

  it("renders the config editor error for the materializations pipeline with pickle input but no subset", async () => {
    await page.goto(
      "http://127.0.0.1:3000/playground/materialization_pipeline/",
      {
        waitUntil: "networkidle0",
      }
    );
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids:\n" +
        "  sort_by_calories:\n" +
        "  inputs:\n" +
        "  cereals:\n" +
        "  pickle:\n" +
        '  path: "/dagster_home/storage/2584d954-a30f-4be6-bbfc-c919e4bee84b/intermediates/read_csv.compute/result"\n'
    );
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(".CodeMirror textarea", "storage:\n" + "  filesystem:\n");
    await page.keyboard.press("Backspace");
    await sleep(500);

    await page.waitForSelector(".CodeMirror-lint-mark-error");
    const image = await page.screenshot({
      path: screenshotPath("/reexecution_errors.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("reexecution_errors"));
    return;
  });

  it("renders the subset selector for the materializations pipeline with pickle input", async () => {
    await page.goto(
      "http://127.0.0.1:3000/playground/materialization_pipeline/",
      {
        waitUntil: "networkidle0",
      }
    );
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids:\n" +
        "  sort_by_calories:\n" +
        "  inputs:\n" +
        "  cereals:\n" +
        "  pickle:\n" +
        '  path: "/dagster_home/storage/2584d954-a30f-4be6-bbfc-c919e4bee84b/intermediates/read_csv.compute/result"\n'
    );
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(".CodeMirror textarea", "storage:\n" + "  filesystem:\n");
    await page.keyboard.press("Backspace");
    await sleep(500);

    await page.waitForSelector(".CodeMirror-lint-mark-error");

    await page.click("button[title=solid-subset-selector]");
    await sleep(100);
    await page.keyboard.press("Backspace");
    await page.type("input[title=graph-query-input]", "sort_by_calories");
    await page.click("input[title=graph-query-input]");
    await page.keyboard.press(" ");

    await sleep(100);
    const image = await page.screenshot({
      path: screenshotPath("/subset_selection.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("subset_selection"));
    return;
  });

  it("renders the playground for the materializations pipeline with pickle input and a solid subset selected", async () => {
    await page.goto(
      "http://127.0.0.1:3000/playground/materialization_pipeline/",
      {
        waitUntil: "networkidle0",
      }
    );
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids:\n" +
        "  sort_by_calories:\n" +
        "  inputs:\n" +
        "  cereals:\n" +
        "  pickle:\n" +
        '  path: "/dagster_home/storage/2584d954-a30f-4be6-bbfc-c919e4bee84b/intermediates/read_csv.compute/result"\n'
    );
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(".CodeMirror textarea", "storage:\n" + "  filesystem:\n");
    await page.keyboard.press("Backspace");

    await sleep(500);

    await page.waitForSelector(".CodeMirror-lint-mark-error");

    await page.click("button[title=solid-subset-selector]");
    await sleep(100);
    await page.keyboard.press("Backspace");
    await page.type("input[title=graph-query-input]", "sort_by_calories");
    await page.click("input[title=graph-query-input]");
    await page.keyboard.press(" ");
    await page.click('button[title="Apply solid query"]');
    await sleep(50);
    await page.waitForSelector('div[title="sort_by_calories.compute"]');
    const image = await page.screenshot({
      path: screenshotPath("/subset_config.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("subset_config"));
    return;
  });
});

describe("for the output materialization pipeline in materializations", () => {
  let browser;
  let page;
  let dagit;

  beforeAll(async (done) => {
    // dagit -f output_materialization.py -n output_materialization_pipeline
    dagit = await runDagit(
      [
        "-f",
        "output_materialization.py",
        "-a",
        "output_materialization_pipeline",
      ],
      3000
    );
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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
    await page.goto(
      "http://127.0.0.1:3000/playground/output_materialization_pipeline/",
      {
        waitUntil: "networkidle0",
      }
    );
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids:\n" +
        "  sort_by_calories:\n" +
        "  inputs:\n" +
        "  cereals:\n" +
        '  csv: "cereal.csv"\n'
    );
    await page.focus(".CodeMirror textarea");
    for (let i = 0; i < 2; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(
      ".CodeMirror textarea",
      "outputs:\n" +
        "  - result:\n" +
        "    csv:\n" +
        '  path: "sorted_cereals.csv"\n' +
        'sep: ";"\n'
    );
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[title="Start execution in a subprocess"]'
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
          expect(image).toMatchImageSnapshot(
            setConfig("output_materializations")
          );
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
    // dagit -f serialization_strategy.py -n serialization_strategy_pipeline
    dagit = await runDagit(
      [
        "-f",
        "serialization_strategy.py",
        "-a",
        "serialization_strategy_pipeline",
      ],
      3000
    );
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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
    await page.goto(
      "http://127.0.0.1:3000/playground/serialization_strategy_pipeline/",
      {
        waitUntil: "networkidle0",
      }
    );
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.type(
      ".CodeMirror textarea",
      "solids:\n" +
        "  read_csv:\n" +
        "  inputs:\n" +
        "  csv_path:\n" +
        '  value: "cereal.csv"\n'
    );
    await page.focus(".CodeMirror textarea");
    for (let i = 0; i < 4; i++) {
      await page.keyboard.press("Backspace");
    }
    await page.type(".CodeMirror textarea", "storage:\n" + "  filesystem:\n");
    await sleep(500);

    const executeButton = await page.waitForSelector(
      'button[title="Start execution in a subprocess"]'
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
          expect(image).toMatchImageSnapshot(
            setConfig("serialization_strategy")
          );
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
    // dagit -f modes.py -n serialization_strategy_pipeline
    dagit = await runDagit(["-f", "modes.py", "-a", "modes_pipeline"], 3000);
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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
    await page.goto("http://127.0.0.1:3000/playground/modes_pipeline/", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

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
    // dagit -f modes.py -n serialization_strategy_pipeline
    dagit = await runDagit(
      ["-f", "presets.py", "-a", "presets_pipeline"],
      3000
    );
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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
    await page.goto("http://127.0.0.1:3000/playground/presets_pipeline/", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.click("button[data-test-id='mode-picker-button']");
    await sleep(50);
    const [devModeItem] = await page.$x(
      '//li//a//div[contains(text(), "dev")]'
    );
    await devModeItem.click();
    await sleep(50);

    await page.click("button[data-test-id='preset-selector-button']");
    await sleep(50);
    const [devPresetItem] = await page.$x(
      '//li//a//div[contains(text(), "dev")]'
    );
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
    // dagit -f modes.py -n serialization_strategy_pipeline
    dagit = await runDagit(["-f", "repos.py", "-a", "define_repo"], 3000);
    browser = await puppeteer.launch({ args: ["--disable-dev-shm-usage"] });
    done();
  });

  afterAll(async (done) => {
    try {
      await browser.close();
    } catch {}
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
    await page.goto("http://127.0.0.1:3005/pipeline/complex_pipeline:/", {
      waitUntil: "networkidle0",
    });
    await sleep(500);

    // this is because localStorage has the stale config!!
    await page.evaluate(() => {
      window.localStorage.clear();
    });
    await page.reload({ waitUntil: "networkidle0" });
    await sleep(500);

    await page.click("button[id='playground-select-pipeline']");
    await sleep(50);

    const image = await page.screenshot({
      path: screenshotPath("/repos.png"),
    });
    expect(image).toMatchImageSnapshot(setConfig("repos"));
  });
});
