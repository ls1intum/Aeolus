package de.tum.cit.ase;

import com.fasterxml.jackson.core.JsonProcessingException;
import de.tum.cit.ase.bamboo.Publisher;
import de.tum.cit.ase.classes.*;
import de.tum.cit.ase.generator.Generator;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.Arrays;
import java.util.Base64;

/**
 * This is the main class of the bamboo-generator, it is responsible for parsing the input and calling the correct
 * methods to generate, and publish the build plan. We support multiple modes of input, from a file, from json
 * and base64 input. The input can be passed as an argument, or as stdin. The intended usage is for this application
 * to be called from the python cli tool in the same repository. For that we use the base64 encoding of the json
 * representation of the windfile. The application is further intended to be stateless, no information is stored
 * and the generation process does not depend on any previous state.
 * The workflow is as follows:
 * 1. Parse the input (either from file, json, base64 or stdin)
 * 2. Generate the build plan
 * 3. Print the build plan to stdout
 * 4. If --publish is passed, publish the build plan to bamboo (specified by --server and --token)
 * <p>
 * For the generation process, we use the bamboo-specs library, which is a library provided by Atlassian to generate
 * build plans for bamboo. We use the library to generate a build plan from the windfile, and then serialize it to
 * yaml, which is then printed to stdout. Every other output needs to be printed to stderr, so that it can be
 * redirected to a file, while the yaml is printed to stdout and can be piped to the python cli tool.
 */

@SpringBootApplication
public class Main {

    private static final String FILE_INPUT_ARGUMENT = "--file";
    private static final String API_ARGUMENT = "--api";
    private static final String STDIN_ARGUMENT = "--stdin";
    private static final String JSON_ARGUMENT = "--json";
    private static final String BASE64_ARGUMENT = "--base64";
    private static final String GET_YAML_ARGUMENT = "--get-yaml";
    private static final String PUBLISH_ARGUMENT = "--publish";
    private static final String BAMBOO_SERVER_ARGUMENT = "--server";
    private static final String BAMBOO_TOKEN_ARGUMENT = "--token";

    private static boolean publish = false;
    private static String bambooUrl = "";
    private static String bambooToken = "";

    /**
     * If --server and --token are passed, we parse them and store them in the static variables
     *
     * @param args the arguments passed to the application
     */
    private static void parseCredentials(String[] args) {
        if (!Arrays.asList(args).contains(BAMBOO_SERVER_ARGUMENT) || !Arrays.asList(args).contains(BAMBOO_TOKEN_ARGUMENT)) {
            System.err.println("If you want to interact with Bamboo, you also have to provide a bamboo server url and a bamboo token");
        }
        bambooUrl = args[Arrays.asList(args).indexOf(BAMBOO_SERVER_ARGUMENT) + 1];
        bambooToken = args[Arrays.asList(args).indexOf(BAMBOO_TOKEN_ARGUMENT) + 1];
    }

    /**
     * If --publish is passed, we parse the credentials and set the publish variable to true, so we know to
     * contact the bamboo server
     *
     * @param args the arguments passed to the application
     */
    private static void parsePublish(String[] args) {
        if (Arrays.asList(args).contains(PUBLISH_ARGUMENT)) {
            publish = true;
            parseCredentials(args);
        }
    }


    private static Mode getMode(String[] args) {
        if (Arrays.asList(args).contains(API_ARGUMENT)) {
            return Mode.API;
        }
        if (Arrays.asList(args).contains(GET_YAML_ARGUMENT)) {
            return Mode.FETCH_YAML;
        }
        return Mode.GENERATION;
    }

    /**
     * This method is used to parse the input and returns the parsed Windfile
     *
     * @param args the arguments passed to the application
     * @return the parsed Windfile
     */
    private static WindFile getInput(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java -jar bamboo-generator.jar " + API_ARGUMENT + "|" + FILE_INPUT_ARGUMENT + "|" + STDIN_ARGUMENT + "|" + JSON_ARGUMENT + "|" + BASE64_ARGUMENT + "|" + GET_YAML_ARGUMENT + " [path|json|base64|buildplankey]" + "--publish --server <bamboo-server-url> --token <bamboo-token>");
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
                    System.err.println("Error reading from stdin, exiting.");
                    System.exit(2);
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

    /**
     * If --get-yaml is passed, we parse the credentials and the build plan key, and then fetch the yaml from bamboo
     * and print it to stdout
     *
     * @param args the arguments passed to the application
     */
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
            case GENERATION -> {
                WindFile windFile = getInput(args);
                Generator generator = new Generator(publish, bambooUrl, bambooToken);
                generator.generateBuildPlan(windFile);
                System.out.println(generator.getResult());
                generator.publish();
            }
            case FETCH_YAML -> getYAML(args);
            case API -> SpringApplication.run(Main.class, args);
        }
    }
}
