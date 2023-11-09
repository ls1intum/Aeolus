package de.tum.cit.ase.classes;


import java.util.Map;
import java.util.Optional;

public class WindFileMetadata {

    private String name;
    private String id;
    private String description;
    private Author author;
    private DockerConfig docker;
    private String gitCredentials;
    private String resultHook;

    public static WindFileMetadata fromMap(Map<String, Object> map) {
        WindFileMetadata metadata = new WindFileMetadata();
        metadata.setName((String) map.get("name"));
        metadata.setDescription((String) map.get("description"));
        Object author = map.get("author");
        metadata.setAuthor(Author.fromObject(author));
        metadata.setGitCredentials((String) map.getOrDefault("gitCredentials", null));
        metadata.setId((String) map.get("id"));
        metadata.setDocker(DockerConfig.fromMap((Map<String, Object>) map.getOrDefault("docker", null)));
        metadata.setResultHook((String) map.getOrDefault("resultHook", null));
        return metadata;
    }

    public String getName() {
        return name;
    }

    private void setName(String name) {
        this.name = name;
    }

    public String getDescription() {
        return description;
    }

    private void setDescription(String description) {
        this.description = description;
    }

    public Author getAuthor() {
        return author;
    }

    private void setAuthor(Author author) {
        this.author = author;
    }

    public String getGitCredentials() {
        return gitCredentials;
    }

    private void setGitCredentials(String gitCredentials) {
        this.gitCredentials = gitCredentials;
    }

    public DockerConfig getDocker() {
        return docker;
    }

    private void setDocker(DockerConfig docker) {
        this.docker = docker;
    }

    public String getId() {
        return id;
    }

    private void setId(String id) {
        this.id = id;
    }

    public String getResultHook() {
        return resultHook;
    }

    public void setResultHook(String resultHook) {
        this.resultHook = resultHook;
    }

    public String getProjectKey() {
        if (getId() == null) {
            return "NOPROJECTKEYSET";
        }
        String id = getId();
        if (id.contains("/")) {
            id = id.replaceAll("/", "-");
        }
        var parts = id.split("-");
        return parts[0];
    }

    public String getPlanName() {
        if (getId() == null) {
            return "NOPROJECTKEYSET";
        }
        String id = getId();
        if (id.contains("/")) {
            id = id.replaceAll("/", "-");
        }
        var parts = id.split("-");
        return parts[1];
    }
}
