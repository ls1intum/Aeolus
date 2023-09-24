package de.tum.cit.ase.classes;

import java.util.List;
import java.util.Map;

public abstract class Action {

    private String name;
    private Map<String, String> parameters;
    private Map<String, String> environment;
    private List<String> excludeDuring;

    public static Action fromMap(String name, Map<String, Object> map) {
        if (map.containsKey("script")) {
            return InternalAction.fromMap(name, map);
        } else {
            return ExternalAction.fromMap(name, map);
        }
    }

    public String getName() {
        return name;
    }

    protected void setName(String name) {
        this.name = name;
    }

    public Map<String, String> getParameters() {
        return parameters;
    }

    protected void setParameters(Map<String, String> parameters) {
        this.parameters = parameters;
    }

    public Map<String, String> getEnvironment() {
        return environment;
    }

    protected void setEnvironment(Map<String, String> environment) {
        this.environment = environment;
    }

    public List<String> getExcludeDuring() {
        return excludeDuring;
    }

    protected void setExcludeDuring(List<String> excludeDuring) {
        this.excludeDuring = excludeDuring;
    }
}
