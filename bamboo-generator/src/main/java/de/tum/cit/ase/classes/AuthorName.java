package de.tum.cit.ase.classes;

import java.util.Optional;

public class AuthorName extends Author {

    public AuthorName(String name) {
        super(name);
    }

    @Override
    public Optional<String> getEmail() {
        return Optional.empty();
    }
}
