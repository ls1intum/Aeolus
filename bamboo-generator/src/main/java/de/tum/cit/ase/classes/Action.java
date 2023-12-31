package de.tum.cit.ase.classes;

import java.util.List;
import java.util.Map;

public abstract class Action {

    private String name;
    private Map<String, Object> parameters;
    private Map<String, String> environment;
    private List<String> excludeDuring;
    private List<Result> results;
    private DockerConfig docker;
    private boolean runAlways;
    private String workdir;

    public static Action fromMap(Map<String, Object> map) {
        if (map.containsKey("kind")) {
            return PlatformAction.fromMap(map);
        } else if (map.containsKey("script")) {
            return ScriptAction.fromMap(map);
        } else {
            return ExternalAction.fromMap(map);
        }
    }

    public String getName() {
        return name;
    }

    protected void setName(String name) {
        this.name = name;
    }

    public Map<String, Object> getParameters() {
        return parameters;
    }

    protected void setParameters(Map<String, Object> parameters) {
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

    public boolean isRunAlways() {
        return runAlways;
    }

    protected void setRunAlways(boolean runAlways) {
        this.runAlways = runAlways;
    }

    public DockerConfig getDocker() {
        return docker;
    }

    protected void setDocker(DockerConfig docker) {
        this.docker = docker;
    }

    public String getWorkdir() {
        return workdir;
    }

    public void setWorkdir(String workdir) {
        this.workdir = workdir;
    }

    public List<Result> getResults() {
        return results;
    }

    public void setResults(List<Result> results) {
        this.results = results;
    }
}
