package de.tum.cit.ase;

import com.atlassian.bamboo.specs.api.builders.BambooKey;
import com.atlassian.bamboo.specs.api.builders.Variable;
import com.atlassian.bamboo.specs.api.builders.plan.Job;
import com.atlassian.bamboo.specs.api.builders.plan.Plan;
import com.atlassian.bamboo.specs.api.builders.plan.Stage;
import com.atlassian.bamboo.specs.api.builders.project.Project;
import com.atlassian.bamboo.specs.api.builders.repository.VcsRepository;
import com.atlassian.bamboo.specs.api.builders.task.Task;
import com.atlassian.bamboo.specs.builders.repository.git.GitRepository;
import com.atlassian.bamboo.specs.builders.task.CheckoutItem;
import com.atlassian.bamboo.specs.builders.task.VcsCheckoutTask;
import com.atlassian.bamboo.specs.util.BambooSpecSerializer;
import com.fasterxml.jackson.core.JsonProcessingException;
import de.tum.cit.ase.bamboo.BuildPlanService;
import de.tum.cit.ase.bamboo.Publisher;
import de.tum.cit.ase.classes.*;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.List;

public class Main {

    private static final String FILE_INPUT_ARGUMENT = "--file";
    private static final String STDIN_ARGUMENT = "--stdin";
    private static final String JSON_ARGUMENT = "--json";
    private static final String BASE64_ARGUMENT = "--base64";
    private static final String GET_YAML_ARGUMENT = "--get-yaml";
    private static final String PUBLISH_ARGUMENT = "--publish";
    private static final String BAMBOOSERVER_ARGUMENT = "--server";
    private static final String BAMBOOTOKEN_ARGUMENT = "--token";

    private static boolean publish = false;
    private static String bambooUrl = "";
    private static String bambooToken = "";

    private static void parseCredentials(String[] args) {
        if (!Arrays.asList(args).contains(BAMBOOSERVER_ARGUMENT) || !Arrays.asList(args).contains(BAMBOOTOKEN_ARGUMENT)) {
            System.err.println("If you want to interact with Bamboo, you also have to provide a bamboo server url and a bamboo token");
        }
        bambooUrl = args[Arrays.asList(args).indexOf(BAMBOOSERVER_ARGUMENT) + 1];
        bambooToken = args[Arrays.asList(args).indexOf(BAMBOOTOKEN_ARGUMENT) + 1];
    }

    private static void parsePublish(String[] args) {
        if (Arrays.asList(args).contains(PUBLISH_ARGUMENT)) {
            publish = true;
            parseCredentials(args);
        }
    }

    private static Mode getMode(String[] args) {
        if (Arrays.asList(args).contains(GET_YAML_ARGUMENT)) {
            return Mode.FETCH_YAML;
        }
        return Mode.GENERATION;
    }

    private static WindFile getInput(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java -jar bamboo-generator.jar " + FILE_INPUT_ARGUMENT + "|" + STDIN_ARGUMENT + "|" + JSON_ARGUMENT + "|" + BASE64_ARGUMENT + "|" + GET_YAML_ARGUMENT + " [path|json|base64|buildplankey]" + "--publish --server <bamboo-server-url> --token <bamboo-token>");
            System.exit(1);
        }
        String source = args[0];
        switch (source) {
            case FILE_INPUT_ARGUMENT -> {
                if (args.length < 2) {
                    System.err.println("If you use a file, you also have to provide a file path");
                }
                parseCredentials(args);
                String filePath = args[1];
                try {
                    return WindFile.fromFile(filePath);
                } catch (FileNotFoundException e) {
                    System.err.println(filePath + " not found, exiting.");
                    System.exit(2);
                }
            }
            case STDIN_ARGUMENT -> {
                StringBuilder builder = new StringBuilder();
                parseCredentials(args);
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(System.in))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        if (line.equals("---EOF---")) {
                            break;
                        }
                        builder.append(line);
                        builder.append("\n");
                    }
                    System.err.println("✅ done reading windfile from stdin");
                } catch (IOException e) {
                    e.printStackTrace();
                }
                try {
                    return WindFile.fromYAML(builder.toString());
                } catch (ClassCastException e) {
                    e.printStackTrace();
                    System.err.println("stdin input was not a correct Windfile, check your syntax");
                    System.exit(2);
                }
            }
            case JSON_ARGUMENT -> {
                if (args.length < 2) {
                    System.err.println("If you use json, you also have to provide a json object");
                }
                parsePublish(args);
                String json = args[1];
                try {
                    return WindFile.fromJson(json);
                } catch (ClassCastException | JsonProcessingException e) {
                    System.err.println("Passed json is not valid, exiting.");
                    System.err.println(json);
                    System.exit(2);
                }
            }
            case BASE64_ARGUMENT -> {
                if (args.length < 2) {
                    System.err.println("If you use base64, you also have to provide a json object encoded in base64");
                }
                parsePublish(args);
                byte[] decoded = Base64.getDecoder().decode(args[1]);
                String json = new String(decoded);
                try {
                    return WindFile.fromJson(json);
                } catch (ClassCastException | JsonProcessingException e) {
                    System.err.println("Passed base64 is not valid, exiting.");
                    System.err.println(json);
                    System.exit(2);
                }
            }
            default -> getInput(new String[]{});
        }
        return null;
    }

    private static void generateBuildPlan(String[] args) {

        WindFile windFile = getInput(args);

        BuildPlanService buildPlanService = new BuildPlanService();
        Project project = new Project().key("AEOLUS").name("AEOLUS").description("aeolus");
        Plan plan = new Plan(project, windFile.getMetadata().getName(), "BASE1")
                .description("Plan created from " + windFile.getFilePath())
                .variables(new Variable("lifecycle_stage", "evaluation"));
        List<Stage> stageList = new ArrayList<>();
        List<GitRepository> repos = new ArrayList<>();
        if (!windFile.getRepositories().isEmpty()) {
            List<VcsCheckoutTask> checkoutTasks = new ArrayList<>();
            for (Repository repository : windFile.getRepositories()) {
                repos.add(buildPlanService.addRepository(repository, windFile.getMetadata().getGitCredentials().orElseThrow()));
                checkoutTasks.add(new VcsCheckoutTask().checkoutItems(new CheckoutItem().repository(repository.getName()).path(repository.getPath())));
            }
            plan = plan.planRepositories(repos.toArray(new VcsRepository[]{}));
            stageList.add(new Stage("Checkout").jobs(new Job("Checkout", "CHECKOUT1").tasks(checkoutTasks.toArray(new Task[]{}))));
        }
        for (Action action : windFile.getActions()) {
            if (action instanceof ExternalAction) {
                continue;
            }
            if (action instanceof InternalAction internalAction) {
                var keyInput = internalAction.getName().toUpperCase().replaceAll("-", "").replaceAll("_", "") + stageList.size();
                var key = new BambooKey(keyInput);
                var tasks = buildPlanService.handleAction(internalAction);
                Stage stage = new Stage(internalAction.getName()).jobs(
                        new Job(internalAction.getName(), key).tasks(
                                tasks.toArray(new Task[]{})
                        ));
                stageList.add(stage);
            }
            if (action instanceof PlatformAction platformAction) {
                var keyInput = platformAction.getName().toUpperCase().replaceAll("-", "").replaceAll("_", "") + stageList.size();
                var key = new BambooKey(keyInput);
                var tasks = buildPlanService.handleSpecialAction(platformAction);
                Stage stage = new Stage(platformAction.getName()).jobs(
                        new Job(platformAction.getName(), key).tasks(
                                tasks.toArray(new Task[]{})
                        ).dockerConfiguration(action.convertDockerConfig()));
                stageList.add(stage);
            }
        }
        plan = plan.stages(stageList.toArray(new Stage[0]));
        final String yaml = BambooSpecSerializer.dump(plan);
        System.err.println("✅ Generation done, printing result to stdout");
        System.out.println(yaml);
    }

    private static void getYAML(String[] args) {
        if (args.length < 2) {
            System.err.println("If you use --get-yaml, you also have to provide a build plan key");
        }
        parseCredentials(args);
        String buildPlanKey = args[Arrays.asList(args).indexOf(GET_YAML_ARGUMENT) + 1];
        Publisher publisher = new Publisher(bambooUrl, bambooToken);
        String planYAML = publisher.getPlanYAML(buildPlanKey);
        System.out.println(planYAML);
    }

    public static void main(String[] args) {
        // we support stdin as input and also filepaths, the default is stdin, a file
        // can be passed if the first argument is --file
        Mode mode = getMode(args);
        switch (mode) {
            case GENERATION -> generateBuildPlan(args);
            case FETCH_YAML -> getYAML(args);
        }
    }
}
