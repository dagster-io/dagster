package io.quicktype;

import com.fasterxml.jackson.annotation.*;
import java.util.Map;

public class Event {
    private String dagsterPipesVersion;
    private Method method;
    private Map<String, Map<String, Object>> params;

    /**
     * The version of the Dagster Pipes protocol
     */
    @JsonProperty("__dagster_pipes_version")
    public String getDagsterPipesVersion() { return dagsterPipesVersion; }
    @JsonProperty("__dagster_pipes_version")
    public void setDagsterPipesVersion(String value) { this.dagsterPipesVersion = value; }

    /**
     * Event type
     */
    @JsonProperty("method")
    public Method getMethod() { return method; }
    @JsonProperty("method")
    public void setMethod(Method value) { this.method = value; }

    /**
     * Event parameters
     */
    @JsonProperty("params")
    public Map<String, Map<String, Object>> getParams() { return params; }
    @JsonProperty("params")
    public void setParams(Map<String, Map<String, Object>> value) { this.params = value; }
}
