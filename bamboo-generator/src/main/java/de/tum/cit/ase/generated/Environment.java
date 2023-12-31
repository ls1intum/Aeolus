
package de.tum.cit.ase.generated;

import javax.annotation.processing.Generated;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyDescription;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


/**
 * Environment Schema
 * <p>
 * Defines the available environment variables that can be used in an aeolus job. To be compliant with aeolus, all environment variables need to be mapped to the corresponding environment variables of the CI system.
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@JsonPropertyOrder({
    "JOB_NAME",
    "JOB_ID",
    "JOB_URI",
    "JOB_URL",
    "RUNNER_NAME",
    "BRANCH_NAME",
    "WORKDIR",
    "TMPDIR",
    "REPOSITORY_URL"
})
@Generated("jsonschema2pojo")
public class Environment {

    /**
     * The name of the job that is currently executed.
     * (Required)
     * 
     */
    @JsonProperty("JOB_NAME")
    @JsonPropertyDescription("The name of the job that is currently executed.")
    private String jobName;
    /**
     * The id of the job that is currently executed.
     * (Required)
     * 
     */
    @JsonProperty("JOB_ID")
    @JsonPropertyDescription("The id of the job that is currently executed.")
    private String jobId;
    /**
     * The identifier of the job that is currently executed.
     * (Required)
     * 
     */
    @JsonProperty("JOB_URI")
    @JsonPropertyDescription("The identifier of the job that is currently executed.")
    private String jobUri;
    /**
     * The url of the result of the job that is currently executed.
     * (Required)
     * 
     */
    @JsonProperty("JOB_URL")
    @JsonPropertyDescription("The url of the result of the job that is currently executed.")
    private String jobUrl;
    /**
     * The name of the runner that is executing the job.
     * (Required)
     * 
     */
    @JsonProperty("RUNNER_NAME")
    @JsonPropertyDescription("The name of the runner that is executing the job.")
    private String runnerName;
    /**
     * The name of the branch that is currently executed.
     * (Required)
     * 
     */
    @JsonProperty("BRANCH_NAME")
    @JsonPropertyDescription("The name of the branch that is currently executed.")
    private String branchName;
    /**
     * The directory where the job is executed.
     * (Required)
     * 
     */
    @JsonProperty("WORKDIR")
    @JsonPropertyDescription("The directory where the job is executed.")
    private String workdir;
    /**
     * The directory where temporary files are stored.
     * (Required)
     * 
     */
    @JsonProperty("TMPDIR")
    @JsonPropertyDescription("The directory where temporary files are stored.")
    private String tmpdir;
    /**
     * The url of the first repository that is used, if multiple repositories are needed, the second one will be referenced under REPOSITORY_URL_1 and so on.
     * (Required)
     * 
     */
    @JsonProperty("REPOSITORY_URL")
    @JsonPropertyDescription("The url of the first repository that is used, if multiple repositories are needed, the second one will be referenced under REPOSITORY_URL_1 and so on.")
    private String repositoryUrl;

    /**
     * No args constructor for use in serialization
     * 
     */
    public Environment() {
    }

    /**
     * 
     * @param jobName
     *     The name of the job that is currently executed.
     * @param tmpdir
     *     The directory where temporary files are stored.
     * @param jobId
     *     The id of the job that is currently executed.
     * @param jobUri
     *     The identifier of the job that is currently executed.
     * @param workdir
     *     The directory where the job is executed.
     * @param runnerName
     *     The name of the runner that is executing the job.
     * @param jobUrl
     *     The url of the result of the job that is currently executed.
     * @param branchName
     *     The name of the branch that is currently executed.
     * @param repositoryUrl
     *     The url of the first repository that is used, if multiple repositories are needed, the second one will be referenced under REPOSITORY_URL_1 and so on.
     */
    public Environment(String jobName, String jobId, String jobUri, String jobUrl, String runnerName, String branchName, String workdir, String tmpdir, String repositoryUrl) {
        super();
        this.jobName = jobName;
        this.jobId = jobId;
        this.jobUri = jobUri;
        this.jobUrl = jobUrl;
        this.runnerName = runnerName;
        this.branchName = branchName;
        this.workdir = workdir;
        this.tmpdir = tmpdir;
        this.repositoryUrl = repositoryUrl;
    }

    /**
     * The name of the job that is currently executed.
     * (Required)
     * 
     */
    @JsonProperty("JOB_NAME")
    public String getJobName() {
        return jobName;
    }

    /**
     * The name of the job that is currently executed.
     * (Required)
     * 
     */
    @JsonProperty("JOB_NAME")
    public void setJobName(String jobName) {
        this.jobName = jobName;
    }

    public Environment withJobName(String jobName) {
        this.jobName = jobName;
        return this;
    }

    /**
     * The id of the job that is currently executed.
     * (Required)
     * 
     */
    @JsonProperty("JOB_ID")
    public String getJobId() {
        return jobId;
    }

    /**
     * The id of the job that is currently executed.
     * (Required)
     * 
     */
    @JsonProperty("JOB_ID")
    public void setJobId(String jobId) {
        this.jobId = jobId;
    }

    public Environment withJobId(String jobId) {
        this.jobId = jobId;
        return this;
    }

    /**
     * The identifier of the job that is currently executed.
     * (Required)
     * 
     */
    @JsonProperty("JOB_URI")
    public String getJobUri() {
        return jobUri;
    }

    /**
     * The identifier of the job that is currently executed.
     * (Required)
     * 
     */
    @JsonProperty("JOB_URI")
    public void setJobUri(String jobUri) {
        this.jobUri = jobUri;
    }

    public Environment withJobUri(String jobUri) {
        this.jobUri = jobUri;
        return this;
    }

    /**
     * The url of the result of the job that is currently executed.
     * (Required)
     * 
     */
    @JsonProperty("JOB_URL")
    public String getJobUrl() {
        return jobUrl;
    }

    /**
     * The url of the result of the job that is currently executed.
     * (Required)
     * 
     */
    @JsonProperty("JOB_URL")
    public void setJobUrl(String jobUrl) {
        this.jobUrl = jobUrl;
    }

    public Environment withJobUrl(String jobUrl) {
        this.jobUrl = jobUrl;
        return this;
    }

    /**
     * The name of the runner that is executing the job.
     * (Required)
     * 
     */
    @JsonProperty("RUNNER_NAME")
    public String getRunnerName() {
        return runnerName;
    }

    /**
     * The name of the runner that is executing the job.
     * (Required)
     * 
     */
    @JsonProperty("RUNNER_NAME")
    public void setRunnerName(String runnerName) {
        this.runnerName = runnerName;
    }

    public Environment withRunnerName(String runnerName) {
        this.runnerName = runnerName;
        return this;
    }

    /**
     * The name of the branch that is currently executed.
     * (Required)
     * 
     */
    @JsonProperty("BRANCH_NAME")
    public String getBranchName() {
        return branchName;
    }

    /**
     * The name of the branch that is currently executed.
     * (Required)
     * 
     */
    @JsonProperty("BRANCH_NAME")
    public void setBranchName(String branchName) {
        this.branchName = branchName;
    }

    public Environment withBranchName(String branchName) {
        this.branchName = branchName;
        return this;
    }

    /**
     * The directory where the job is executed.
     * (Required)
     * 
     */
    @JsonProperty("WORKDIR")
    public String getWorkdir() {
        return workdir;
    }

    /**
     * The directory where the job is executed.
     * (Required)
     * 
     */
    @JsonProperty("WORKDIR")
    public void setWorkdir(String workdir) {
        this.workdir = workdir;
    }

    public Environment withWorkdir(String workdir) {
        this.workdir = workdir;
        return this;
    }

    /**
     * The directory where temporary files are stored.
     * (Required)
     * 
     */
    @JsonProperty("TMPDIR")
    public String getTmpdir() {
        return tmpdir;
    }

    /**
     * The directory where temporary files are stored.
     * (Required)
     * 
     */
    @JsonProperty("TMPDIR")
    public void setTmpdir(String tmpdir) {
        this.tmpdir = tmpdir;
    }

    public Environment withTmpdir(String tmpdir) {
        this.tmpdir = tmpdir;
        return this;
    }

    /**
     * The url of the first repository that is used, if multiple repositories are needed, the second one will be referenced under REPOSITORY_URL_1 and so on.
     * (Required)
     * 
     */
    @JsonProperty("REPOSITORY_URL")
    public String getRepositoryUrl() {
        return repositoryUrl;
    }

    /**
     * The url of the first repository that is used, if multiple repositories are needed, the second one will be referenced under REPOSITORY_URL_1 and so on.
     * (Required)
     * 
     */
    @JsonProperty("REPOSITORY_URL")
    public void setRepositoryUrl(String repositoryUrl) {
        this.repositoryUrl = repositoryUrl;
    }

    public Environment withRepositoryUrl(String repositoryUrl) {
        this.repositoryUrl = repositoryUrl;
        return this;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append(Environment.class.getName()).append('@').append(Integer.toHexString(System.identityHashCode(this))).append('[');
        sb.append("jobName");
        sb.append('=');
        sb.append(((this.jobName == null)?"<null>":this.jobName));
        sb.append(',');
        sb.append("jobId");
        sb.append('=');
        sb.append(((this.jobId == null)?"<null>":this.jobId));
        sb.append(',');
        sb.append("jobUri");
        sb.append('=');
        sb.append(((this.jobUri == null)?"<null>":this.jobUri));
        sb.append(',');
        sb.append("jobUrl");
        sb.append('=');
        sb.append(((this.jobUrl == null)?"<null>":this.jobUrl));
        sb.append(',');
        sb.append("runnerName");
        sb.append('=');
        sb.append(((this.runnerName == null)?"<null>":this.runnerName));
        sb.append(',');
        sb.append("branchName");
        sb.append('=');
        sb.append(((this.branchName == null)?"<null>":this.branchName));
        sb.append(',');
        sb.append("workdir");
        sb.append('=');
        sb.append(((this.workdir == null)?"<null>":this.workdir));
        sb.append(',');
        sb.append("tmpdir");
        sb.append('=');
        sb.append(((this.tmpdir == null)?"<null>":this.tmpdir));
        sb.append(',');
        sb.append("repositoryUrl");
        sb.append('=');
        sb.append(((this.repositoryUrl == null)?"<null>":this.repositoryUrl));
        sb.append(',');
        if (sb.charAt((sb.length()- 1)) == ',') {
            sb.setCharAt((sb.length()- 1), ']');
        } else {
            sb.append(']');
        }
        return sb.toString();
    }

    @Override
    public int hashCode() {
        int result = 1;
        result = ((result* 31)+((this.jobName == null)? 0 :this.jobName.hashCode()));
        result = ((result* 31)+((this.tmpdir == null)? 0 :this.tmpdir.hashCode()));
        result = ((result* 31)+((this.jobId == null)? 0 :this.jobId.hashCode()));
        result = ((result* 31)+((this.jobUri == null)? 0 :this.jobUri.hashCode()));
        result = ((result* 31)+((this.workdir == null)? 0 :this.workdir.hashCode()));
        result = ((result* 31)+((this.runnerName == null)? 0 :this.runnerName.hashCode()));
        result = ((result* 31)+((this.jobUrl == null)? 0 :this.jobUrl.hashCode()));
        result = ((result* 31)+((this.branchName == null)? 0 :this.branchName.hashCode()));
        result = ((result* 31)+((this.repositoryUrl == null)? 0 :this.repositoryUrl.hashCode()));
        return result;
    }

    @Override
    public boolean equals(Object other) {
        if (other == this) {
            return true;
        }
        if ((other instanceof Environment) == false) {
            return false;
        }
        Environment rhs = ((Environment) other);
        return ((((((((((this.jobName == rhs.jobName)||((this.jobName!= null)&&this.jobName.equals(rhs.jobName)))&&((this.tmpdir == rhs.tmpdir)||((this.tmpdir!= null)&&this.tmpdir.equals(rhs.tmpdir))))&&((this.jobId == rhs.jobId)||((this.jobId!= null)&&this.jobId.equals(rhs.jobId))))&&((this.jobUri == rhs.jobUri)||((this.jobUri!= null)&&this.jobUri.equals(rhs.jobUri))))&&((this.workdir == rhs.workdir)||((this.workdir!= null)&&this.workdir.equals(rhs.workdir))))&&((this.runnerName == rhs.runnerName)||((this.runnerName!= null)&&this.runnerName.equals(rhs.runnerName))))&&((this.jobUrl == rhs.jobUrl)||((this.jobUrl!= null)&&this.jobUrl.equals(rhs.jobUrl))))&&((this.branchName == rhs.branchName)||((this.branchName!= null)&&this.branchName.equals(rhs.branchName))))&&((this.repositoryUrl == rhs.repositoryUrl)||((this.repositoryUrl!= null)&&this.repositoryUrl.equals(rhs.repositoryUrl))));
    }

}
