package de.tum.cit.ase.api.controller;

import de.tum.cit.ase.api.interfaces.GeneratorApi;
import de.tum.cit.ase.api.payload.GeneratorPayload;
import de.tum.cit.ase.classes.WindFile;
import de.tum.cit.ase.generator.Generator;
import de.tum.cit.ase.utils.Utils;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.RequestBody;

import java.util.HashMap;
import java.util.Map;

@Service
public class GeneratorController implements GeneratorApi {

    @Override
    public ResponseEntity<?> healthz() {
        return ResponseEntity.ok("OK");
    }

    @Override
    public ResponseEntity<?> generate(@RequestBody GeneratorPayload payload) {
        WindFile windFile;
        try {
            windFile = Utils.getWindFile(payload);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }

        var timestamp = System.currentTimeMillis();
        Generator generator = new Generator(false, null, null);
        generator.generateBuildPlan(windFile);
        System.out.println("Generation took for " + generator.getKey() + " " + (System.currentTimeMillis() - timestamp) + "ms");
        Map<String, String> result = new HashMap<>();
        result.put("result", generator.getResult());
        result.put("key", generator.getKey());
        return ResponseEntity.ok(result);
    }
}
