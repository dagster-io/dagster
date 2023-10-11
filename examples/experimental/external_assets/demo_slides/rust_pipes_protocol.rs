struct PipesContext {
    partition_key: String,
    // omitting other properties for brevity
}

fn open_dagster_pipes() -> PipesContext
{
    let param = env::var("DAGSTER_PIPES_CONTEXT").unwrap();
    let zlib_compressed_slice = base64::decode(param).unwrap();
    let mut decoder = ZlibDecoder::new(&zlib_compressed_slice[..]);
    let mut json_str = String::new();
    decoder.read_to_string(&mut json_str).unwrap();
    let pipes: PipesContext = serde_json::from_str(&json_str).unwrap();
    return pipes;
}


struct PipesMessage {
    __dagster_pipes_version: String,
    method: String,
    params: Option<HashMap<String, serde_json::Value>>,
}

fn report_asset_check(
    pipes: &mut PipesContext,
    check_name: &str,
    passed: bool,
    asset_key: &str,
    metadata: serde_json::Value,
) {
    let params: HashMap<String, serde_json::Value> = HashMap::from([
        ("asset_key".to_string(), json!(asset_key)),
        ("check_name".to_string(), json!(check_name)),
        ("passed".to_string(), json!(passed)),
        ("severity".to_string(), json!("ERROR")), 
        ("metadata".to_string(), metadata),
    ]);

    let msg = PipesMessage {
        __dagster_pipes_version: "0.1".to_string(),
        method: "report_asset_check".to_string(),
        params: Some(params),
    };
    let serialized_msg = serde_json::to_string(&msg).unwrap();
    eprintln!("{}", serialized_msg);
}