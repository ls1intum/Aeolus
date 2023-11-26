package de.tum.cit.ase.classes;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class PlatformAction extends Action {

    private String kind;

    public static PlatformAction fromMap(Map<String, Object> map) {
        PlatformAction action = new PlatformAction();
        action.setName((String) map.get("name"));
        action.setKind((String) map.get("kind"));
        action.setParameters((Map<String, Object>) map.getOrDefault("parameters", new HashMap<>()));
        action.setEnvironment((Map<String, String>) map.getOrDefault("environment", new HashMap<>()));
        action.setExcludeDuring((List<String>) map.getOrDefault("excludeDuring", new ArrayList<>()));
        action.setRunAlways((boolean) map.getOrDefault("runAlways", false));
        action.setWorkdir((String) map.getOrDefault("workdir", null));
        action.setDocker(DockerConfig.fromMap((Map<String, Object>) map.getOrDefault("docker", new HashMap<>())));
        action.setResults(Result.fromList((List<Object>) map.getOrDefault("results", new ArrayList<>())));
        return action;
    }

    public String getKind() {
        return kind;
    }

    public void setKind(String kind) {
        this.kind = kind;
    }
}
