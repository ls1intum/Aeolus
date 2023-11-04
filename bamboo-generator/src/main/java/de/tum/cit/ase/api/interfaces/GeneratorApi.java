package de.tum.cit.ase.api.interfaces;

import de.tum.cit.ase.api.payload.GeneratorPayload;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController()
public interface GeneratorApi {

    @GetMapping(path="/healthz")
    ResponseEntity<?> healthz();

    @PostMapping(path="/generate",
            consumes = {"application/x-yaml", "application/yaml", "application/json"})
    ResponseEntity<?> generate(@RequestBody GeneratorPayload body);
}
