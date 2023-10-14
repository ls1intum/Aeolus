package de.tum.cit.ase.classes;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class ExternalAction extends Action {

    private String use;

    public static ExternalAction fromMap(String name, Map<String, Object> map) {
        ExternalAction action = new ExternalAction();
        action.setName(name);
        action.setUse((String) map.get("use"));
        action.setParameters((Map<String, Object>) map.getOrDefault("parameters", new HashMap<>()));
        action.setEnvironment((Map<String, String>) map.getOrDefault("environment", new HashMap<>()));
        action.setExcludeDuring((List<String>) map.getOrDefault("excludeDuring", new ArrayList<>()));
        action.setRunAlways((boolean) map.getOrDefault("run_always", false));
        action.setDocker(DockerConfig.fromMap((Map<String, Object>) map.getOrDefault("docker", new HashMap<>())));
        return action;
    }

    public String getUse() {
        return use;
    }

    private void setUse(String use) {
        this.use = use;
    }
}
