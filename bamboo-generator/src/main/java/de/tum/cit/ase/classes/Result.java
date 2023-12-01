package de.tum.cit.ase.classes;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class Result {

    private String name;
    private String path;
    private String ignore;
    private String type;
    private boolean before;

    public Result(String name, String path, String ignore, String type, boolean before) {
        this.name = name;
        this.path = path;
        this.ignore = ignore;
        this.type = type;
        this.before = before;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getPath() {
        return path;
    }

    public void setPath(String path) {
        this.path = path;
    }

    public String getIgnore() {
        return ignore;
    }

    public void setIgnore(String ignore) {
        this.ignore = ignore;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public static List<Result> fromList(List<Object> resultsList) {
        if (resultsList == null || resultsList.isEmpty()) {
            return new ArrayList<>();
        }
        List<Result> results = new ArrayList<>();
        for (Object result : resultsList) {
            if (result instanceof Map) {
                Map<String, Object> resultMap = (Map<String, Object>) result;
                String name = (String) resultMap.getOrDefault("name", null);
                String path = (String) resultMap.getOrDefault("path", null);
                String ignore = (String) resultMap.getOrDefault("ignore", null);
                String type = (String) resultMap.getOrDefault("type", null);
                Boolean bool = (Boolean) resultMap.getOrDefault("boolean", false);
                if (bool == null) {
                    bool = false;
                }
                results.add(new Result(name, path, ignore, type, bool));
            }
        }
        return results;
    }

    public boolean isBefore() {
        return before;
    }

    public void setBefore(boolean before) {
        this.before = before;
    }
}
