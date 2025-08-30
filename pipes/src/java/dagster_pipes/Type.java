package io.quicktype;

import java.io.IOException;
import com.fasterxml.jackson.annotation.*;

public enum Type {
    ASSET, BOOL, DAGSTER_RUN, FLOAT, INFER, INT, JSON, MD, NOTEBOOK, NULL, PATH, TEXT, URL;

    @JsonValue
    public String toValue() {
        switch (this) {
            case ASSET: return "asset";
            case BOOL: return "bool";
            case DAGSTER_RUN: return "dagster_run";
            case FLOAT: return "float";
            case INFER: return "__infer__";
            case INT: return "int";
            case JSON: return "json";
            case MD: return "md";
            case NOTEBOOK: return "notebook";
            case NULL: return "null";
            case PATH: return "path";
            case TEXT: return "text";
            case URL: return "url";
        }
        return null;
    }

    @JsonCreator
    public static Type forValue(String value) throws IOException {
        if (value.equals("asset")) return ASSET;
        if (value.equals("bool")) return BOOL;
        if (value.equals("dagster_run")) return DAGSTER_RUN;
        if (value.equals("float")) return FLOAT;
        if (value.equals("__infer__")) return INFER;
        if (value.equals("int")) return INT;
        if (value.equals("json")) return JSON;
        if (value.equals("md")) return MD;
        if (value.equals("notebook")) return NOTEBOOK;
        if (value.equals("null")) return NULL;
        if (value.equals("path")) return PATH;
        if (value.equals("text")) return TEXT;
        if (value.equals("url")) return URL;
        throw new IOException("Cannot deserialize Type");
    }
}
