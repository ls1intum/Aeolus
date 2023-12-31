package de.tum.cit.ase.generator;

import com.atlassian.bamboo.specs.api.builders.AtlassianModule;
import com.atlassian.bamboo.specs.api.builders.BambooKey;
import com.atlassian.bamboo.specs.api.builders.Variable;
import com.atlassian.bamboo.specs.api.builders.notification.AnyNotificationRecipient;
import com.atlassian.bamboo.specs.api.builders.notification.Notification;
import com.atlassian.bamboo.specs.api.builders.plan.Job;
import com.atlassian.bamboo.specs.api.builders.plan.Plan;
import com.atlassian.bamboo.specs.api.builders.plan.Stage;
import com.atlassian.bamboo.specs.api.builders.plan.artifact.Artifact;
import com.atlassian.bamboo.specs.api.builders.plan.branches.BranchCleanup;
import com.atlassian.bamboo.specs.api.builders.plan.branches.PlanBranchManagement;
import com.atlassian.bamboo.specs.api.builders.plan.configuration.ConcurrentBuilds;
import com.atlassian.bamboo.specs.api.builders.project.Project;
import com.atlassian.bamboo.specs.api.builders.repository.VcsRepository;
import com.atlassian.bamboo.specs.api.builders.task.Task;
import com.atlassian.bamboo.specs.builders.notification.PlanCompletedNotification;
import com.atlassian.bamboo.specs.builders.repository.git.GitRepository;
import com.atlassian.bamboo.specs.builders.task.CheckoutItem;
import com.atlassian.bamboo.specs.builders.task.VcsCheckoutTask;
import com.atlassian.bamboo.specs.util.BambooSpecSerializer;
import de.tum.cit.ase.bamboo.BuildPlanService;
import de.tum.cit.ase.bamboo.Publisher;
import de.tum.cit.ase.classes.*;
import de.tum.cit.ase.utils.Utils;
import org.springframework.lang.NonNull;

import java.util.ArrayList;
import java.util.List;

public class Generator {


    private boolean publish = false;
    private String bambooUrl = "";
    private String bambooToken = "";
    private String result = "";
    private Plan plan;
    private Project project;

    public Generator(boolean publish, String bambooUrl, String bambooToken) {
        this.publish = publish;
        this.bambooUrl = bambooUrl;
        this.bambooToken = bambooToken;
    }

    /**
     * If no docker configuration is specified, we can put all tasks in one stage, this is easier to read
     *
     * @param windFile the parsed Windfile
     * @return true if all tasks can be put in one stage, false otherwise
     */
    private static boolean canBePutInOneStage(WindFile windFile) {
        return windFile.getActions().stream().noneMatch(action -> action.getDocker() != null);
    }

    /**
     * This method is used to create a project object from the metadata of the windfile.
     *
     * @param metadata the metadata of the windfile
     * @return a project object
     */
    private static Project getEmptyProject(WindFileMetadata metadata) {
        String id = metadata.getProjectKey();
        return new Project().key(id.toUpperCase()).name(metadata.getName()).description(metadata.getDescription() + "\n---created using aeolus");
    }

    /**
     * This method is used to generate the build plan from the parsed Windfile, it creates a bamboo plan that
     * consists of a checkout task (if repositories are specified), and a task for each action in the Windfile.
     * If the given Windfile contains a docker configuration, the tasks are run in the specified docker container.
     *
     * @param windFile the parsed Windfile
     */
    public void generateBuildPlan(@NonNull WindFile windFile) {

        BuildPlanService buildPlanService = new BuildPlanService();
        project = getEmptyProject(windFile.getMetadata());
        String planKey = Utils.getBambooKeyOf(windFile.getMetadata().getPlanName());
        String name = windFile.getMetadata().getPlanName();
        System.out.println("Generating plan " + planKey);
        System.out.println("Generating project " + name);
        plan = new Plan(project, name, planKey).description(windFile.getMetadata().getDescription())
                .variables(new Variable("lifecycle_stage", "working_time"))
                .pluginConfigurations(new ConcurrentBuilds().useSystemWideDefault(true))
                .planBranchManagement(new PlanBranchManagement().delete(new BranchCleanup()).notificationForCommitters());
        if (windFile.getMetadata().getResultHook() != null) {
            plan = plan.notifications(new Notification().type(new PlanCompletedNotification())
                    .recipients(new AnyNotificationRecipient(new AtlassianModule("de.tum.in.www1.bamboo-server:recipient.server"))
                            .recipientString(windFile.getMetadata().getResultHook())));
        }
        boolean oneStageIsEnough = canBePutInOneStage(windFile);

        Stage defaultStage = new Stage("Default Stage");
        Job defaultJob = new Job("Default Job", new BambooKey("JOB1"));
        if (oneStageIsEnough) {
            var docker = BuildPlanService.convertDockerConfig(windFile.getMetadata().getDocker());
            if (docker != null) {
                defaultJob.dockerConfiguration(docker);
            }
        }

        List<Stage> stageList = new ArrayList<>();
        List<GitRepository> repos = new ArrayList<>();

        if (!windFile.getRepositories().isEmpty()) {
            List<CheckoutItem> checkoutItems = new ArrayList<>();
            for (Repository repository : windFile.getRepositories()) {
                repos.add(buildPlanService.addRepository(repository, windFile.getMetadata().getGitCredentials()));
                checkoutItems.add(new CheckoutItem().repository(repository.getName()).path(repository.getPath()));
            }
            VcsCheckoutTask checkoutTask = new VcsCheckoutTask().description("Checkout Default Repository").checkoutItems(checkoutItems.toArray(new CheckoutItem[]{})).cleanCheckout(true);
            plan = plan.planRepositories(repos.toArray(new VcsRepository[]{}));
            if (oneStageIsEnough) {
                defaultJob.tasks(checkoutTask);
            } else {
                stageList.add(new Stage("Checkout").jobs(new Job("Checkout", "CHECKOUT1").tasks(checkoutTask)));
            }
        }
        /*
         * If we have one global docker configuration, we run every single task in the same docker container
         * this means we need only one stage and one job with all tasks in it
         */
        List<Task<?, ?>> defaultTasks = new ArrayList<>();
        List<Task<?, ?>> defaultFinalTasks = new ArrayList<>();
        for (Action action : windFile.getActions()) {
            if (action instanceof ExternalAction) {
                continue;
            }
            if (oneStageIsEnough) {
                defaultJob = this.addArtifacts(defaultJob, action);
            }
            var keyInput = action.getName().toUpperCase().replaceAll("[^a-zA-Z0-9]", "") + stageList.size();
            var key = new BambooKey(keyInput);
            List<Task<?, ?>> tasks = new ArrayList<>();
            if (action instanceof ScriptAction scriptAction) {
                tasks = buildPlanService.handleAction(scriptAction);
            } else if (action instanceof PlatformAction platformAction) {
                tasks = buildPlanService.handleSpecialAction(platformAction);
            }
            if (oneStageIsEnough) {
                if (action.isRunAlways()) {
                    defaultFinalTasks.addAll(tasks);
                } else {
                    defaultTasks.addAll(tasks);
                }
            } else {
                var job = new Job(action.getName(), key);
                if (action.isRunAlways()) {
                    job = job.finalTasks(tasks.toArray(new Task[]{}));
                } else {
                    job = job.tasks(tasks.toArray(new Task[]{}));
                }
                var docker = BuildPlanService.convertDockerConfig(action.getDocker());
                if (docker != null) {
                    job = job.dockerConfiguration(docker);
                }
                job = this.addArtifacts(job, action);
                Stage stage = new Stage(action.getName().replaceAll("[^a-zA-Z0-9]", "")).jobs(
                        job
                );
                stageList.add(stage);
            }
        }
        if (oneStageIsEnough) {
            defaultJob.tasks(defaultTasks.toArray(new Task[]{}));
            defaultJob.finalTasks(defaultFinalTasks.toArray(new Task[]{}));
            defaultStage.jobs(defaultJob);
            stageList.add(defaultStage);
        }
        plan = plan.stages(stageList.toArray(new Stage[]{}));
        result = BambooSpecSerializer.dump(plan);
    }

    /**
     * This method is used to add the artifacts to the job, it is used to add the artifacts to the default job
     * if we only have one stage, and to add the artifacts to the job of the stage if we have multiple stages.
     * If the result is of type "junit", we add the junit parser to the job in other parts of the application.
     *
     * @param job    the job to add the artifacts to
     * @param action the action that contains the artifacts
     * @return the job with the artifacts added
     */
    public Job addArtifacts(Job job, Action action) {
        if (action.getResults() == null) {
            return job;
        }
        List<Artifact> artifacts = new ArrayList<>();
        for (Result result : action.getResults()) {
            if ("junit".equals(result.getType())) {
                // junit parser is added as a task
                continue;
            }
            try {
                var pathComponents = result.getPath().split("/");
                var pattern = result.getPath();
                var path = "";
                if (pathComponents.length > 1) {
                    pattern = pathComponents[pathComponents.length - 1];
                    path = result.getPath().substring(0, result.getPath().length() - pattern.length() - 1);
                }
                Artifact artifact = new Artifact().name(result.getName()).copyPatterns(pattern).location(path).shared(false).required(false);
                if (result.getIgnore() != null) {
                    artifact = artifact.exclusionPatterns(result.getIgnore());
                }
                artifacts.add(artifact);
            } catch (Exception e) {
                System.err.println("Error while adding artifact " + result.getName() + " to job " + job.getKey());
                e.printStackTrace();
            }
        }
        job = job.artifacts(artifacts.toArray(new Artifact[]{}));
        return job;
    }

    public String getResult() {
        return result;
    }

    public String getKey() {
        return project.getKey() + "-" + plan.getKey();
    }

    public void publish() {
        if (publish) {
            Publisher publisher = new Publisher(bambooUrl, bambooToken);
            publisher.publish(plan);
            System.err.println("✅ Published to Bamboo");
        }
    }
}
