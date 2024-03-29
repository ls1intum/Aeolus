package de.tum.cit.ase.bamboo;

import com.atlassian.bamboo.specs.api.builders.AtlassianModule;
import com.atlassian.bamboo.specs.api.builders.condition.AnyTaskCondition;
import com.atlassian.bamboo.specs.api.builders.credentials.SharedCredentialsIdentifier;
import com.atlassian.bamboo.specs.api.builders.credentials.SharedCredentialsScope;
import com.atlassian.bamboo.specs.api.builders.docker.DockerConfiguration;
import com.atlassian.bamboo.specs.api.builders.repository.VcsChangeDetection;
import com.atlassian.bamboo.specs.api.builders.task.Task;
import com.atlassian.bamboo.specs.builders.repository.git.GitRepository;
import com.atlassian.bamboo.specs.builders.task.ScriptTask;
import com.atlassian.bamboo.specs.builders.task.TestParserTask;
import de.tum.cit.ase.classes.DockerConfig;
import de.tum.cit.ase.classes.ScriptAction;
import de.tum.cit.ase.classes.PlatformAction;
import de.tum.cit.ase.classes.Repository;

import java.util.*;
import java.util.stream.Collectors;

public class BuildPlanService {

    public static DockerConfiguration convertDockerConfig(DockerConfig docker) {
        if (docker == null) {
            return null;
        }
        String dockerImage = docker.getImage();
        if (!dockerImage.contains(":") && docker.getTag() == null) {
            dockerImage += ":latest";
        } else if (docker.getTag() != null) {
            dockerImage += ":" + docker.getTag();
        }
        DockerConfiguration configuration = new DockerConfiguration()
                .image(dockerImage)
                .dockerRunArguments(docker.getParameters().toArray(new String[0]));
        for (Map.Entry<String, String> entry : docker.getVolumes().entrySet()) {
            configuration.volume(entry.getKey(), entry.getValue());
        }
        return configuration;
    }

    public GitRepository addRepository(Repository repository, String credentialsName) {
        GitRepository repo = new GitRepository();
        if (credentialsName != null) {
            repo.authentication(new SharedCredentialsIdentifier(credentialsName)
                    .scope(SharedCredentialsScope.GLOBAL));
        }
        return repo
                .name(repository.getName())
                .branch(repository.getBranch())
                .url(repository.getUrl())
                .shallowClonesEnabled(true)
                .remoteAgentCacheEnabled(false)
                .changeDetection(new VcsChangeDetection());
    }

    public List<Task<?, ?>> handleSpecialAction(PlatformAction action) {
        var tasks = new ArrayList<Task<?, ?>>();

        String type = action.getKind();
        if (type.equals("junit")) {
            Object parameters = action.getParameters().get("test_results");
            String param = String.valueOf(parameters);
            if (parameters instanceof List) {
                List<String> results = (List<String>) parameters;
                param = String.join(",", results);
            }
            TestParserTask task = TestParserTask.createJUnitParserTask()
                    .description(action.getName())
                    .resultDirectories(param);
            tasks.add(task);
        }
        return tasks;
    }

    public List<Task<?, ?>> handleAction(ScriptAction action) {
        var tasks = new ArrayList<Task<?, ?>>();
        var envs = Arrays.stream(action.getEnvironment().entrySet().stream()
                .map(entry -> entry.getKey() + "=" + entry.getValue())
                .toArray(String[]::new)).reduce((a, b) -> a + ";" + b).orElse("");

        String script = "#!/usr/bin/env bash\n" + action.getScript();
        ScriptTask task = new ScriptTask()
                .description(action.getName())
                .inlineBody(script);

        var parameters = action.getParameters();
        String params = "";

        if (parameters != null && !parameters.isEmpty()) {
            params = Arrays.stream(parameters.entrySet().stream()
                    .map(entry -> entry.getKey() + "=" + entry.getValue())
                    .toArray(String[]::new)).reduce((a, b) -> a + ";" + b).orElse("");
        }

        if (action.getWorkdir() != null) {
            task = task.workingSubdirectory(action.getWorkdir());
        }

        if (!action.getExcludeDuring().isEmpty()) {
            String postfix = action.getExcludeDuring().isEmpty() ? "" : " if stage is correct";
            String dummyTask = "echo \"⚙️ Executing " + action.getName() + postfix + "\"";
            tasks.add(new ScriptTask().description("dummy task to prevent wrong result of build plan run")
                    .inlineBody(dummyTask));
            var condMap = new HashMap<String, String>();
            condMap.put("operation", "matches");
            condMap.put("variable", "lifecycle_stage");
            var regex = action.getExcludeDuring().stream().map(stage -> "[^(" + stage + ")]").collect(Collectors.joining());
            condMap.put("value", "^.*" + regex + ".*");
            var condition = new AnyTaskCondition(
                    new AtlassianModule(
                            "com.atlassian.bamboo.plugins.bamboo-conditional-tasks:variableCondition")
            ).configuration(condMap);
            task = task.conditions(condition);
        }
        if (!envs.isEmpty() || !params.isEmpty()) {
            String all = envs.isEmpty() ? params : envs + ";" + params;
            task = task.environmentVariables(all);
        }
        tasks.add(task);
        return tasks;
    }
}
