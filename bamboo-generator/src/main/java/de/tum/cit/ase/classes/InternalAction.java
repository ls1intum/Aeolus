package de.tum.cit.ase.classes;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class InternalAction extends Action {

    private String script;

    public static Action fromMap(String name, Map<String, Object> map) {
        InternalAction action = new InternalAction();
        action.setName(name);
        action.setScript((String) map.get("script"));
        action.setParameters((Map<String, String>) map.getOrDefault("parameters", new HashMap<>()));
        action.setEnvironment((Map<String, String>) map.getOrDefault("environment", new HashMap<>()));
        action.setExcludeDuring((List<String>) map.getOrDefault("excludeDuring", new ArrayList<>()));
        return action;
    }

    public String getScript() {
        return script;
    }

    private void setScript(String script) {
        this.script = script;
    }
}
