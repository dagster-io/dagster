package io.quicktype;

import com.fasterxml.jackson.annotation.*;
import java.util.Map;

public class ProvenanceByAssetKey {
    private String codeVersion;
    private Map<String, String> inputDataVersions;
    private Boolean isUserProvided;

    @JsonProperty("code_version")
    public String getCodeVersion() { return codeVersion; }
    @JsonProperty("code_version")
    public void setCodeVersion(String value) { this.codeVersion = value; }

    @JsonProperty("input_data_versions")
    public Map<String, String> getInputDataVersions() { return inputDataVersions; }
    @JsonProperty("input_data_versions")
    public void setInputDataVersions(Map<String, String> value) { this.inputDataVersions = value; }

    @JsonProperty("is_user_provided")
    public Boolean getIsUserProvided() { return isUserProvided; }
    @JsonProperty("is_user_provided")
    public void setIsUserProvided(Boolean value) { this.isUserProvided = value; }
}
