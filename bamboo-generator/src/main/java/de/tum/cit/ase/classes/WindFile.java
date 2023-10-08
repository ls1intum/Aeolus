package de.tum.cit.ase.classes;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLMapper;
import org.yaml.snakeyaml.Yaml;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class WindFile {

    private String filePath;
    private String api;
    private WindFileMetadata metadata;
    private List<Repository> repositories = new ArrayList<>();
    private List<Action> actions = new ArrayList<>();
    private Map<String, Map<String, Map<String, String>>> preProcessingMetadata = new HashMap<>();

    public static WindFile fromJson(String json) throws ClassCastException, JsonProcessingException {
        JsonNode jsonNodeTree = new ObjectMapper().readTree(json);
        String yaml = new YAMLMapper().writeValueAsString(jsonNodeTree);
        return fromYAML(yaml);
    }

    public static WindFile fromYAML(String yaml) throws ClassCastException {
        Map<String, Object> data = new Yaml().load(yaml);
        WindFile windfile = new WindFile();
        windfile.setFilePath("stdin");
        windfile.setApi(data.get("api").toString());
        windfile.setMetadata(WindFileMetadata.fromMap((Map<String, Object>) data.get("metadata")));
        Map<String, Object> repositories = (Map<String, Object>) data.getOrDefault("repositories", new HashMap<String, Object>());
        for (Map.Entry<String, Object> repository : repositories.entrySet()) {
            Map<String, Object> repoMap = (Map<String, Object>) repository.getValue();
            windfile.appendRepository(Repository.fromMap(repository.getKey(), repoMap));
        }
        Map<String, Object> actions = (Map<String, Object>) data.get("actions");
        for (Map.Entry<String, Object> action : actions.entrySet()) {
            Map<String, Object> actionMap = (Map<String, Object>) action.getValue();
            windfile.appendAction(Action.fromMap(action.getKey(), actionMap));
        }
        return windfile;
    }

    public static WindFile fromFile(String filePath) throws FileNotFoundException {
        InputStream inputStream = new FileInputStream(filePath);

        Yaml yaml = new Yaml();
        Map<String, Object> data = yaml.load(inputStream);
        return fromYAML(yaml.dump(data));
    }

    public String getFilePath() {
        return filePath;
    }

    private void setFilePath(String filePath) {
        this.filePath = filePath;
    }

    public String getApi() {
        return api;
    }

    private void setApi(String api) {
        this.api = api;
    }

    public WindFileMetadata getMetadata() {
        return metadata;
    }

    public void setMetadata(WindFileMetadata metadata) {
        this.metadata = metadata;
    }

    public void appendAction(Action action) {
        this.actions.add(action);
    }

    public void appendRepository(Repository repository) {
        this.repositories.add(repository);
    }

    public List<Action> getActions() {
        return actions;
    }

    public void setActions(List<Action> actions) {
        this.actions = actions;
    }

    public List<Repository> getRepositories() {
        return repositories;
    }

    public void setRepositories(List<Repository> repositories) {
        this.repositories = repositories;
    }

    public Map<String, Map<String, Map<String, String>>> getPreProcessingMetadata() {
        return preProcessingMetadata;
    }

    public void setPreProcessingMetadata(Map<String, Map<String, Map<String, String>>> preProcessingMetadata) {
        this.preProcessingMetadata = preProcessingMetadata;
    }
}
