package de.tum.cit.ase.classes;

import java.util.Map;

public class Repository {

    private String name;
    private String url;
    private String branch;
    private String path;

    public static Repository fromMap(String name, Map<String, Object> map) {
        Repository action = new Repository();
        action.setName(name);
        action.setUrl((String) map.get("url"));
        action.setPath((String) map.getOrDefault("path", "."));
        action.setBranch((String) map.get("branch"));
        return action;
    }

    public String getName() {
        return name;
    }

    private void setName(String name) {
        this.name = name;
    }

    public String getUrl() {
        return url;
    }

    private void setUrl(String url) {
        this.url = url;
    }

    public String getBranch() {
        return branch;
    }

    private void setBranch(String branch) {
        this.branch = branch;
    }

    public String getPath() {
        return path;
    }

    private void setPath(String path) {
        this.path = path;
    }
}
