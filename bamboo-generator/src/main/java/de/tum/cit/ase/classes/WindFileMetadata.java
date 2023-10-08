package de.tum.cit.ase.classes;


import java.util.Map;
import java.util.Optional;

public class WindFileMetadata {

    private String name;
    private String description;
    private Author author;
    private DockerConfig docker;
    private Optional<String> gitCredentials;

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }

    public Author getAuthor() {
        return author;
    }

    public Optional<String> getGitCredentials() {
        return gitCredentials;
    }

    private void setName(String name) {
        this.name = name;
    }

    private void setDescription(String description) {
        this.description = description;
    }

    private void setAuthor(Author author) {
        this.author = author;
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

    public static WindFileMetadata fromMap(Map<String, Object> map) {
        WindFileMetadata metadata = new WindFileMetadata();
        metadata.setName((String) map.get("name"));
        metadata.setDescription((String) map.get("description"));
        Object author = map.get("author");
        metadata.setAuthor(Author.fromObject(author));
        metadata.setGitCredentials(Optional.ofNullable((String) map.get("gitCredentials")));
        metadata.setDocker(DockerConfig.fromMap((Map<String, Object>) map.getOrDefault("docker", null)));
        return metadata;
    }
}
