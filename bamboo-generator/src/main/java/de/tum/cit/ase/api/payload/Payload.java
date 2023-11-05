package de.tum.cit.ase.api.payload;

public abstract class Payload {

    protected String windfile;

    public Payload() {
    }

    public String getWindfile() {
        return windfile;
    }

    public void setWindfile(String windfile) {
        this.windfile = windfile;
    }
}
