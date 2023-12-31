package de.tum.cit.ase.classes;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class ScriptAction extends Action {

    private String script;

    public static Action fromMap(Map<String, Object> map) {
        ScriptAction action = new ScriptAction();
        action.setName((String) map.get("name"));
        action.setScript((String) map.get("script"));
        action.setParameters((Map<String, Object>) map.getOrDefault("parameters", new HashMap<>()));
        action.setEnvironment((Map<String, String>) map.getOrDefault("environment", new HashMap<>()));
        action.setExcludeDuring((List<String>) map.getOrDefault("excludeDuring", new ArrayList<>()));
        action.setRunAlways((boolean) map.getOrDefault("runAlways", false));
        action.setWorkdir((String) map.getOrDefault("workdir", null));
        action.setDocker(DockerConfig.fromMap((Map<String, Object>) map.getOrDefault("docker", new HashMap<>())));
        action.setResults(Result.fromList((List<Object>) map.getOrDefault("results", new ArrayList<>())));
        return action;
    }

    public String getScript() {
        return script;
    }

    private void setScript(String script) {
        this.script = script;
    }
}
