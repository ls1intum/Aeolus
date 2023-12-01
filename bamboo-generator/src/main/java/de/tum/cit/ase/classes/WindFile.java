package de.tum.cit.ase.classes;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLMapper;
import de.tum.cit.ase.utils.Utils;
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

    private String api;
    private WindFileMetadata metadata;
    private List<Repository> repositories = new ArrayList<>();
    private List<Action> actions = new ArrayList<>();

    public static WindFile fromJson(String json) throws ClassCastException, JsonProcessingException {
        JsonNode jsonNodeTree = new ObjectMapper().readTree(json);
        String yaml = new YAMLMapper().writeValueAsString(jsonNodeTree);
        return fromYAML(yaml);
    }

    public static WindFile fromYAML(String yaml) throws ClassCastException {
        Map<String, Object> data = new Yaml().load(yaml);
        WindFile windfile = new WindFile();
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
    private static PlatformAction getResultAction(Action action, List<Result> results) {
        Result result = results.get(0);
        PlatformAction newResultAction = new PlatformAction();
        newResultAction.setRunAlways(action.isRunAlways());
        newResultAction.setKind("junit");
        newResultAction.setName(Utils.getBambooKeyOf(action.getName() + "-" + result.getName()));
        List<String> paths = results.stream().map(Result::getPath).toList();
        if (action.getWorkdir() != null) {
            paths = paths.stream().map(p -> action.getWorkdir() + "/" + p).toList();
        }
        Map<String, Object> parameters = new HashMap<>();
        parameters.put("test_results", paths);
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
            if (results.isEmpty() || results.stream().noneMatch(r -> "junit".equals(r.getType()))) {
                newActions.add(action);
                continue;
            }
            List<Result> resultsToReplace = results.stream().filter(r -> "junit".equals(r.getType())).toList();
            if (resultsToReplace.isEmpty()) {
                newActions.add(action);
                continue;
            }
            List<Result> beforeResults = results.stream().filter(Result::isBefore).toList();
            List<Result> afterResults = results.stream().filter(r -> !r.isBefore()).toList();
            PlatformAction beforeResultsAction = getResultAction(action, beforeResults);
            PlatformAction afterResultsAction = getResultAction(action, afterResults);
            action.setResults(results.stream().filter(r -> !"junit".equals(r.getType())).toList());
            newActions.add(beforeResultsAction);
            newActions.add(action);
            newActions.add(afterResultsAction);
        }
        this.setActions(newActions);
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
}
