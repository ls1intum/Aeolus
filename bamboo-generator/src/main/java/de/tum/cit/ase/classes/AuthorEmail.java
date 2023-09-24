package de.tum.cit.ase.classes;

import java.util.Optional;

public class AuthorEmail extends Author {

    private String email;

    public AuthorEmail(String name, String email) {
        super(name);
        this.email = email;
    }

    public Optional<String> getEmail() {
        return Optional.of(email);
    }
}
