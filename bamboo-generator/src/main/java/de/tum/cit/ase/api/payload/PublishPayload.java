package de.tum.cit.ase.api.payload;

public class PublishPayload extends Payload {

    private String url;
    private String username;
    private String token;

    public PublishPayload() {
    }

    public PublishPayload(String url, String token, String windfile) {
        this.url = url;
        this.token = token;
        this.windfile = windfile;
    }

    public String getUrl() {
        return url;
    }

    public void setUrl(String url) {
        this.url = url;
    }

    public String getToken() {
        return token;
    }

    public void setToken(String token) {
        this.token = token;
    }

    public String getUsername() {
        return username;
    }
}
