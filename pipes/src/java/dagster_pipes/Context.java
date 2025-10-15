package io.quicktype;

import com.fasterxml.jackson.annotation.*;
import java.util.Map;

/**
 * The serializable data passed from the orchestration process to the external process. This
 * gets wrapped in a PipesContext.
 */
public class Context {
    private String[] assetKeys;
    private Map<String, String> codeVersionByAssetKey;
    private Map<String, Object> extras;
    private String jobName;
    private String partitionKey;
    private PartitionKeyRange partitionKeyRange;
    private PartitionTimeWindow partitionTimeWindow;
    private Map<String, ProvenanceByAssetKey> provenanceByAssetKey;
    private long retryNumber;
    private String runID;

    @JsonProperty("asset_keys")
    public String[] getAssetKeys() { return assetKeys; }
    @JsonProperty("asset_keys")
    public void setAssetKeys(String[] value) { this.assetKeys = value; }

    @JsonProperty("code_version_by_asset_key")
    public Map<String, String> getCodeVersionByAssetKey() { return codeVersionByAssetKey; }
    @JsonProperty("code_version_by_asset_key")
    public void setCodeVersionByAssetKey(Map<String, String> value) { this.codeVersionByAssetKey = value; }

    @JsonProperty("extras")
    public Map<String, Object> getExtras() { return extras; }
    @JsonProperty("extras")
    public void setExtras(Map<String, Object> value) { this.extras = value; }

    @JsonProperty("job_name")
    public String getJobName() { return jobName; }
    @JsonProperty("job_name")
    public void setJobName(String value) { this.jobName = value; }

    @JsonProperty("partition_key")
    public String getPartitionKey() { return partitionKey; }
    @JsonProperty("partition_key")
    public void setPartitionKey(String value) { this.partitionKey = value; }

    @JsonProperty("partition_key_range")
    public PartitionKeyRange getPartitionKeyRange() { return partitionKeyRange; }
    @JsonProperty("partition_key_range")
    public void setPartitionKeyRange(PartitionKeyRange value) { this.partitionKeyRange = value; }

    @JsonProperty("partition_time_window")
    public PartitionTimeWindow getPartitionTimeWindow() { return partitionTimeWindow; }
    @JsonProperty("partition_time_window")
    public void setPartitionTimeWindow(PartitionTimeWindow value) { this.partitionTimeWindow = value; }

    @JsonProperty("provenance_by_asset_key")
    public Map<String, ProvenanceByAssetKey> getProvenanceByAssetKey() { return provenanceByAssetKey; }
    @JsonProperty("provenance_by_asset_key")
    public void setProvenanceByAssetKey(Map<String, ProvenanceByAssetKey> value) { this.provenanceByAssetKey = value; }

    @JsonProperty("retry_number")
    public long getRetryNumber() { return retryNumber; }
    @JsonProperty("retry_number")
    public void setRetryNumber(long value) { this.retryNumber = value; }

    @JsonProperty("run_id")
    public String getRunID() { return runID; }
    @JsonProperty("run_id")
    public void setRunID(String value) { this.runID = value; }
}
