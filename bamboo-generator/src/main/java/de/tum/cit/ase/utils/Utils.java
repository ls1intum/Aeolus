package de.tum.cit.ase.utils;

import de.tum.cit.ase.api.payload.Payload;
import de.tum.cit.ase.classes.WindFile;

public class Utils {

    public static WindFile getWindFile(Payload payload) throws IllegalArgumentException {
        WindFile windFile = null;
        try {
            windFile = WindFile.fromYAML(payload.getWindfile());
        } catch (Exception ignored) {

        }
        if (windFile == null) {
            try {
                windFile = WindFile.fromJson(payload.getWindfile());
            } catch (Exception e) {
                throw new IllegalArgumentException("Invalid input" + e.getMessage());
            }
        }
        return windFile;
    }
}
