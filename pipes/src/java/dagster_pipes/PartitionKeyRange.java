package io.quicktype;

import com.fasterxml.jackson.annotation.*;

public class PartitionKeyRange {
    private String end;
    private String start;

    @JsonProperty("end")
    public String getEnd() { return end; }
    @JsonProperty("end")
    public void setEnd(String value) { this.end = value; }

    @JsonProperty("start")
    public String getStart() { return start; }
    @JsonProperty("start")
    public void setStart(String value) { this.start = value; }
}
