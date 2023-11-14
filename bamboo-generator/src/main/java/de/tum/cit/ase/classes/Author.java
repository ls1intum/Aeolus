package de.tum.cit.ase.classes;

import java.util.Map;
import java.util.Optional;

public abstract class Author {

    protected String name;

    public Author(String name) {
        this.name = name;
    }

    public static Author fromObject(Object object) {
        if (object == null) {
            return null;
        } else if (object instanceof String) {
            return new AuthorName((String) object);
        } else if (object instanceof Map) {
            Map<String, String> map = (Map<String, String>) object;
            return new AuthorEmail(map.get("name"), map.get("email"));
        } else {
            throw new IllegalArgumentException("Author must be either a string or a map");
        }
    }

    public String getName() {
        return name;
    }

    abstract Optional<String> getEmail();
}
