package de.tum.cit.ase.classes;


import java.util.Map;
import java.util.Optional;

public class WindFileMetadata {

    private String name;
    private String id;
    private String description;
    private Author author;
    private DockerConfig docker;
    private Optional<String> gitCredentials;

    public static WindFileMetadata fromMap(Map<String, Object> map) {
        WindFileMetadata metadata = new WindFileMetadata();
        metadata.setName((String) map.get("name"));
        metadata.setDescription((String) map.get("description"));
        Object author = map.get("author");
        metadata.setAuthor(Author.fromObject(author));
        metadata.setGitCredentials(Optional.ofNullable((String) map.get("gitCredentials")));
        metadata.setId((String) map.get("id"));
        metadata.setDocker(DockerConfig.fromMap((Map<String, Object>) map.getOrDefault("docker", null)));
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

    public Optional<String> getGitCredentials() {
        return gitCredentials;
    }

    private void setGitCredentials(Optional<String> gitCredentials) {
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

    public String getProjectKey() {
        String id = getId();
        if (id.contains("/")) {
            id = id.replaceAll("/", "-");
        }
        var parts = id.split("-");
        return parts[0];
    }

    public String getPlanName() {
        String id = getId();
        if (id.contains("/")) {
            id = id.replaceAll("/", "-");
        }
        var parts = id.split("-");
        return parts[1];
    }
}
