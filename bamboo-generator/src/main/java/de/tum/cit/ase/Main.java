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
import de.tum.cit.ase.classes.*;

import java.io.*;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;

public class Main {

    private static final String FILE_INPUT_ARGUMENT = "--file";
    private static final String STDIN_ARGUMENT = "--stdin";
    private static final String JSON_ARGUMENT = "--json";
    private static final String BASE64_ARGUMENT = "--base64";

    private static WindFile getInput(String[] args) {
        System.err.println("Starting generation");
        if (args.length < 1) {
            System.err.println("Usage: java -jar bamboo-generator.jar " + FILE_INPUT_ARGUMENT + "|" + STDIN_ARGUMENT);
            System.exit(1);
        }
        String source = args[0];
        switch (source) {
            case FILE_INPUT_ARGUMENT -> {
                if (args.length < 2) {
                    System.err.println("If you use a file, you also have to provide a file path");
                }
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

    public static void main(String[] args) {
        // we support stdin as input and also filepaths, the default is stdin, a file
        // can be passed if the first argument is --file

        WindFile windFile = getInput(args);
//        if (args.length == 2) {
//            String metadataPath = args[1];
//            Gson gson = new Gson();
//            Type mapType = new TypeToken<Map<String, Map<String, Map<String, String>>>>() {
//            }.getType();
//            JsonReader reader = new JsonReader(new FileReader(metadataPath));
//            Map<String, Map<String, Map<String, String>>> metamap = gson.fromJson(reader, mapType);
//            windFile.setPreProcessingMetadata(metamap);
//        }
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
            InternalAction internalAction = (InternalAction) action;
            var keyInput = internalAction.getName().toUpperCase().replaceAll("-", "") + stageList.size();
            var key = new BambooKey(keyInput);
            var tasks = buildPlanService.handleAction(internalAction);
            Stage stage = new Stage(internalAction.getName()).jobs(
                    new Job(internalAction.getName(), key).tasks(
                            tasks.toArray(new Task[]{})
                    ));
            stageList.add(stage);
        }
        plan = plan.stages(stageList.toArray(new Stage[0]));
        final String yaml = BambooSpecSerializer.dump(plan);
        System.err.println("✅ Generation done, printing result to stdout");
        System.out.println(yaml);
    }
}
