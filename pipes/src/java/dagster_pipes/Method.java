package io.quicktype;

import java.io.IOException;
import com.fasterxml.jackson.annotation.*;

/**
 * Event type
 */
public enum Method {
    CLOSED, LOG, OPENED, REPORT_ASSET_CHECK, REPORT_ASSET_MATERIALIZATION, REPORT_CUSTOM_MESSAGE;

    @JsonValue
    public String toValue() {
        switch (this) {
            case CLOSED: return "closed";
            case LOG: return "log";
            case OPENED: return "opened";
            case REPORT_ASSET_CHECK: return "report_asset_check";
            case REPORT_ASSET_MATERIALIZATION: return "report_asset_materialization";
            case REPORT_CUSTOM_MESSAGE: return "report_custom_message";
        }
        return null;
    }

    @JsonCreator
    public static Method forValue(String value) throws IOException {
        if (value.equals("closed")) return CLOSED;
        if (value.equals("log")) return LOG;
        if (value.equals("opened")) return OPENED;
        if (value.equals("report_asset_check")) return REPORT_ASSET_CHECK;
        if (value.equals("report_asset_materialization")) return REPORT_ASSET_MATERIALIZATION;
        if (value.equals("report_custom_message")) return REPORT_CUSTOM_MESSAGE;
        throw new IOException("Cannot deserialize Method");
    }
}
