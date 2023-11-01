package de.tum.cit.ase.api;

import de.tum.cit.ase.classes.WindFile;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController()
public interface GenerationApi {

    @GetMapping(path="/healthz")
    ResponseEntity<?> healthz();

    @PostMapping(path="/generate",
            consumes = {"application/x-yaml", "application/yaml", "application/json"})
    ResponseEntity<?> generate(@RequestBody String body);
}
