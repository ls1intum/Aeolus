package de.tum.cit.ase.api;

import de.tum.cit.ase.classes.WindFile;
import de.tum.cit.ase.generator.Generator;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.RequestBody;

@Service
public class GeneratorController implements GenerationApi {

    @Override
    public ResponseEntity<?> healthz() {
        return ResponseEntity.ok("OK");
    }

    @Override
    public ResponseEntity<?> generate(@RequestBody String body) {
        System.out.println("service called");
        System.out.println(body);
        WindFile windFile = null;
        try {
            windFile = WindFile.fromYAML(body);
        } catch (Exception ignored) {

        }
        if (windFile == null) {
            try {
                windFile = WindFile.fromJson(body);
            } catch (Exception e) {
                return ResponseEntity.badRequest().body("Invalid input" + e.getMessage());
            }
        }
        var timestamp = System.currentTimeMillis();
        Generator generator = new Generator(false, null, null);
        generator.generateBuildPlan(windFile);
        System.out.println("Generation took " + (System.currentTimeMillis() - timestamp) + "ms");
        return ResponseEntity.ok(generator.getResult());
    }
}
