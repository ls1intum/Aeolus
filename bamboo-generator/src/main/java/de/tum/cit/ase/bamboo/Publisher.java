package de.tum.cit.ase.bamboo;

import com.atlassian.bamboo.specs.api.builders.plan.Plan;
import com.atlassian.bamboo.specs.util.BambooServer;
import com.atlassian.bamboo.specs.util.SimpleTokenCredentials;
import com.atlassian.bamboo.specs.util.TokenCredentials;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import org.w3c.dom.Document;
import org.xml.sax.SAXException;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import java.io.ByteArrayInputStream;
import java.io.IOException;

public class Publisher {

    private final BambooServer bambooServer;
    private final String bambooUrl;
    private final String token;

    public Publisher(String url, String token) {
        this.bambooUrl = url;
        this.token = token;
        TokenCredentials tokenCredentials = new SimpleTokenCredentials(token);
        bambooServer = new BambooServer(url, tokenCredentials);
    }

    public void publish(Plan plan) {
        try {
            bambooServer.publish(plan);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public String getPlanYAML(String buildPlanKey) {
        try {
            OkHttpClient client = new OkHttpClient();

            Request request = new Request.Builder()
                    .url(bambooUrl + "/rest/api/latest/plan/" + buildPlanKey + "/specs?all&format=yaml")
                    .header("Authorization", "Bearer " + token)
                    .build();

            Response response = client.newCall(request).execute();

            String responseString = response.body().string();
            DocumentBuilderFactory factory =
                    DocumentBuilderFactory.newInstance();
            DocumentBuilder builder = factory.newDocumentBuilder();
            ByteArrayInputStream input = new ByteArrayInputStream(
                    responseString.getBytes("UTF-8"));
            Document doc = builder.parse(input);
            return doc.getFirstChild().getFirstChild().getFirstChild().getTextContent();
        } catch (IOException | ParserConfigurationException | SAXException e) {
            throw new RuntimeException(e);
        }
    }
}
