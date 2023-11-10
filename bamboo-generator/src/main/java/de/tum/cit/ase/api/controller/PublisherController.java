package de.tum.cit.ase.api.controller;

import de.tum.cit.ase.api.interfaces.PublisherApi;
import de.tum.cit.ase.api.payload.PublishPayload;
import de.tum.cit.ase.classes.WindFile;
import de.tum.cit.ase.generator.Generator;
import de.tum.cit.ase.utils.Utils;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.RequestBody;

import java.util.HashMap;
import java.util.Map;

@Service
public class PublisherController implements PublisherApi {

    @Override
    public ResponseEntity<?> publish(@RequestBody PublishPayload payload) {
        WindFile windFile;
        try {
            windFile = Utils.getWindFile(payload);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }

        var timestamp = System.currentTimeMillis();
        Generator generator = new Generator(true, payload.getUrl(), payload.getToken());
        generator.generateBuildPlan(windFile);
        System.out.println("Generating took " + (System.currentTimeMillis() - timestamp) + "ms");
        timestamp = System.currentTimeMillis();
        try {
            generator.publish();
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.badRequest().body("Publishing failed: " + e.getMessage());
        }
        System.out.println("Publishing took " + (System.currentTimeMillis() - timestamp) + "ms");
        Map<String, String> result = new HashMap<>();
        result.put("result", generator.getResult());
        result.put("key", generator.getKey());
        return ResponseEntity.ok(result);
    }
}
