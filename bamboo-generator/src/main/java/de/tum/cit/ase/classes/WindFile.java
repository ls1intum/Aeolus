package de.tum.cit.ase.classes;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLMapper;
import org.jetbrains.annotations.NotNull;
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
        List<Object> actions = (List<Object>) data.get("actions");
        for (Object action : actions) {
            Map<String, Object> actionMap = (Map<String, Object>) action;
            windfile.appendAction(Action.fromMap(actionMap));
        }
        windfile.convertJunitResultsToActions();
        return windfile;
    }

    @NotNull
    private static PlatformAction getResultAction(Action action, Result result) {
        PlatformAction newResultAction = new PlatformAction();
        newResultAction.setRunAlways(action.isRunAlways());
        newResultAction.setKind("junit");
        newResultAction.setName(action.getName() + "-" + result.getName());
        String path = result.getPath();
        if (action.getWorkdir() != null) {
            path = action.getWorkdir() + "/" + path;
        }
        Map<String, Object> parameters = new HashMap<>();
        parameters.put("test_results", path);
        parameters.put("ignore_time", false);
        newResultAction.setParameters(parameters);
        newResultAction.setEnvironment(action.getEnvironment());
        newResultAction.setExcludeDuring(action.getExcludeDuring());
        newResultAction.setEnvironment(action.getEnvironment());
        newResultAction.setDocker(action.getDocker());
        return newResultAction;
    }

    public static WindFile fromFile(String filePath) throws FileNotFoundException {
        InputStream inputStream = new FileInputStream(filePath);

        Yaml yaml = new Yaml();
        Map<String, Object> data = yaml.load(inputStream);
        return fromYAML(yaml.dump(data));
    }

    private void convertJunitResultsToActions() {
        List<Action> newActions = new ArrayList<>();
        for (Action action : this.getActions()) {
            List<Result> results = action.getResults();
            if (results.isEmpty() || results.stream().noneMatch(r -> r.getType().equals("junit"))) {
                newActions.add(action);
                continue;
            }
            List<Result> resultsToReplace = results.stream().filter(r -> "junit".equals(r.getType())).toList();
            for (Result result : resultsToReplace) {
                PlatformAction newResultAction = getResultAction(action, result);
                newActions.add(newResultAction);
            }
            action.setResults(results.stream().filter(r -> !"junit".equals(r.getType())).toList());
        }
        this.setActions(newActions);
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
