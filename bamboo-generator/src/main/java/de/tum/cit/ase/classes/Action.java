package de.tum.cit.ase.classes;

import com.atlassian.bamboo.specs.api.builders.docker.DockerConfiguration;

import java.util.List;
import java.util.Map;

public abstract class Action {

    private String name;
    private Map<String, String> parameters;
    private Map<String, String> environment;
    private List<String> excludeDuring;
    private DockerConfig docker;
    private boolean always;

    public static Action fromMap(String name, Map<String, Object> map) {
        if (map.containsKey("kind")) {
            return PlatformAction.fromMap(name, map);
        } else if (map.containsKey("script")) {
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

    public boolean isAlways() {
        return always;
    }

    protected void setAlways(boolean always) {
        this.always = always;
    }

    public DockerConfig getDocker() {
        return docker;
    }

    protected void setDocker(DockerConfig docker) {
        this.docker = docker;
    }

    public DockerConfiguration convertDockerConfig() {
        if (docker == null) {
            return null;
        }
        DockerConfiguration configuration = new DockerConfiguration()
                .image(docker.getImage() + ":" + docker.getTag())
                .dockerRunArguments(docker.getParameters().toArray(new String[0]));
        for (Map.Entry<String, String> entry : docker.getVolumes().entrySet()) {
            configuration.volume(entry.getKey(), entry.getValue());
        }
        return configuration;
    }
}
