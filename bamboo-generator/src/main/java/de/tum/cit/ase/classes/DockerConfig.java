package de.tum.cit.ase.classes;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class DockerConfig {

    private String image;
    private String tag;
    private Map<String, String> volumes;
    private List<String> parameters;

    public static DockerConfig fromMap(Map<String, Object> map) {
        if (map == null || map.isEmpty()) {
            return null;
        }
        DockerConfig dockerConfig = new DockerConfig();
        dockerConfig.setImage((String) map.get("image"));
        dockerConfig.setTag((String) map.getOrDefault("tag", "latest"));
        ArrayList<String> volumes = (ArrayList<String>) map.getOrDefault("volumes", new ArrayList<>());
        HashMap<String, String> volumesMap = new HashMap<>();
        for (String volume : volumes) {
            String[] split = volume.split(":");
            if (split.length == 2) {
                volumesMap.put(split[0], split[1]);
            }
        }
        dockerConfig.setVolumes(volumesMap);
        dockerConfig.setParameters((List<String>) map.getOrDefault("parameters", new ArrayList<>()));
        return dockerConfig;
    }

    private void setImage(String image) {
        this.image = image;
    }

    private void setTag(String tag) {
        this.tag = tag;
    }

    private void setVolumes(Map<String, String> volumes) {
        this.volumes = volumes;
    }

    private void setParameters(List<String> parameters) {
        this.parameters = parameters;
    }

    public String getImage() {
        return image;
    }

    public String getTag() {
        return tag;
    }

    public Map<String, String> getVolumes() {
        return volumes;
    }

    public List<String> getParameters() {
        return parameters;
    }
}
