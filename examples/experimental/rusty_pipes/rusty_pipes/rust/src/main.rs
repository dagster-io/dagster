use std::env;

use std::collections::HashMap;

use flate2::read::ZlibDecoder;
use serde::{de, Deserialize, Serialize};
use serde_json::json;
use std::fs::File;
use std::io::prelude::*;
use std::io::BufReader;
use std::io::{self, Write};

#[derive(Debug, Deserialize)]
struct PipesDataProvenance {
    code_version: String,
    input_data_versions: HashMap<String, String>,
    is_user_provided: bool,
}

#[derive(Debug, Deserialize)]
struct PipesPartitionKeyRange {
    start: String,
    end: String,
}

#[derive(Debug, Deserialize)]
struct PipesTimeWindow {
    start: String, // timestamp
    end: String,   // timestamp
}

#[derive(Debug, Deserialize)]
struct PipesContextData {
    asset_keys: Option<Vec<String>>,
    code_version_by_asset_key: Option<HashMap<String, Option<String>>>,
    provenance_by_asset_key: Option<HashMap<String, Option<PipesDataProvenance>>>,
    partition_key: Option<String>,
    partition_key_range: Option<PipesPartitionKeyRange>,
    partition_time_window: Option<PipesTimeWindow>,
    run_id: String,
    job_name: Option<String>,
    retry_number: i32,
    extras: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Deserialize)]
struct PipesContextPayload {
    data: Option<PipesContextData>, // direct in env var
    path: Option<String>,           // load from file
}

#[derive(Debug, Deserialize)]
struct PipesMessagesConfig {
    path: Option<String>,  // write to file
    stdio: Option<String>, // stderr | stdout (unsupported)
}

#[derive(Debug, Serialize)]
struct PipesMessage {
    __dagster_pipes_version: String,
    method: String,
    params: Option<HashMap<String, serde_json::Value>>,
}

#[derive(Debug)]
struct PipesFileMessageWriter {
    file: File,
}

impl PipesFileMessageWriter {
    fn new(path: &str) -> PipesFileMessageWriter {
        let file = File::create(path).unwrap();
        return Self { file };
    }

    fn write_message(&mut self, message: PipesMessage) {
        writeln!(
            &mut self.file,
            "{}",
            serde_json::to_string(&message).unwrap()
        );
    }
}

#[derive(Debug)]
struct PipesContext {
    data: PipesContextData,
    writer: PipesFileMessageWriter, // should be trait & support stdio
}

impl PipesContext {
    fn report_asset_check(
        &mut self,
        check_name: &str,
        passed: bool,
        asset_key: &str,
        metadata: serde_json::Value,
    ) {
        let params: HashMap<String, serde_json::Value> = HashMap::from([
            ("asset_key".to_string(), json!(asset_key)),
            ("check_name".to_string(), json!(check_name)),
            ("passed".to_string(), json!(passed)),
            ("severity".to_string(), json!("ERROR")), // hardcode for now
            ("metadata".to_string(), metadata),
        ]);

        let msg = PipesMessage {
            __dagster_pipes_version: "0.1".to_string(),
            method: "report_asset_check".to_string(),
            params: Some(params),
        };
        self.writer.write_message(msg);
    }
}

fn load_pipes_param<T>(param: &str) -> T
where
    T: de::DeserializeOwned,
{
    let zlib_compressed_slice = base64::decode(param).unwrap();
    let mut decoder = ZlibDecoder::new(&zlib_compressed_slice[..]);
    let mut json_str = String::new();
    decoder.read_to_string(&mut json_str).unwrap();
    let value: T = serde_json::from_str(&json_str).unwrap();
    return value;
}

fn load_pipes_context_data(param: &str) -> PipesContextData {
    let context_payload: PipesContextPayload = load_pipes_param(&param);

    if let Some(context_data) = context_payload.data {
        return context_data;
    } else if let Some(context_path) = context_payload.path {
        let file = File::open(context_path).unwrap();
        let reader = BufReader::new(file);
        let data: PipesContextData = serde_json::from_reader(reader).unwrap();
        return data;
    } else {
        panic!("unable to load dagster pipes context data")
    }
}

fn load_pipes_message_writer(param: &str) -> PipesFileMessageWriter {
    let messages_config: PipesMessagesConfig = load_pipes_param(&param);
    if let Some(path) = messages_config.path {
        return PipesFileMessageWriter::new(&path);
    }
    panic!("Unable to load pipes message writer. Only file based is currently supported")
}

fn get_dagster_pipes_context() -> PipesContext {
    let context_param = env::var("DAGSTER_PIPES_CONTEXT").unwrap();
    let context_data = load_pipes_context_data(&context_param);
    let messages_param = env::var("DAGSTER_PIPES_MESSAGES").unwrap();
    let message_writer = load_pipes_message_writer(&messages_param);
    return PipesContext {
        data: context_data,
        writer: message_writer,
    };
}

fn main() {
    let mut context = get_dagster_pipes_context();
    let metadata = json!({"null_count": {"raw_value": 0, "type": "int"}});
    context.report_asset_check("rust_null_check", true, "some_dataframe", metadata);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_direct_env_var() {
        let sample_value = "eJyNkNFOwzAMRX+l8jOVBm03sV9ByHITBwKtMznpSlX135dsiEmIBx7vvefallewlAiO1QoUIyf85CVm+QIxKceIsYHXhwpMsIxn1uiDYL/gD3yt3tljJdMwbLlx0nBmITH8T540+VTG36ji/7ZRSd74rzD5kXH2YsN8j3US9DZreHq25rHrXN0Yc6jbbu/qvt1zbZzrqKGDdQ1DbnyEHoXGsgIQ+fTOIysN3+eXFAumnHRBmcaeNaO7bPFXUiqfW7dtuwBu9nXw";
        let context_data = load_pipes_context_data(sample_value);
        assert_eq!(
            context_data.asset_keys,
            Some(vec![String::from("stress_s3")])
        )
    }

    #[test]
    fn test_default_process_client_context() {
        let sample_ctx_value = "eJyrVipILMlQslJQ0i9LLNJPy89JSS0q1i8x1DfJTrM0q7AwNTVKSjdIKzNJyTbINsvLyTUAgvQ8/RD9ktyCCuNk8+zSvHL95Py8ktSKEqVaABRGGqc=";
        let path = "/var/folders/t1/4kf96x8552bg0fv4dk0k6nlm0000gn/T/tmpx3c7kunw/context";
        let content = r#"{"asset_keys": null, "code_version_by_asset_key": null, "provenance_by_asset_key": null, "partition_key": null, "partition_key_range": null, "partition_time_window": null, "run_id": "374a5e46-501a-433a-b885-268156faeae9", "job_name": "__ASSET_JOB", "retry_number": 0, "extras": {"path": "/var/folders/t1/4kf96x8552bg0fv4dk0k6nlm0000gn/T/some_dataframe.csv"}}"#;
        let mut file = File::create(path).unwrap();
        file.write_all(content.as_bytes()).unwrap();

        let context_data = load_pipes_context_data(sample_ctx_value);
        assert!(
            context_data.extras.get("path").is_some(),
            "Expect path extra"
        );
    }

    #[test]
    fn test_default_process_client_writer() {
        let sample_msg_value = "eJwNwYsJgCAQANBV4hY4C5VsjhYw/BR+Ek8siHav9x4ouu2wDIBdV3RnNLYSthF5cEresxDT5pnr3AQWZI6J/XzGFVsqVxDtEKQwWSLtLcH7AS2DGsU=";
        let _msg_writer = load_pipes_message_writer(sample_msg_value);
    }
}
