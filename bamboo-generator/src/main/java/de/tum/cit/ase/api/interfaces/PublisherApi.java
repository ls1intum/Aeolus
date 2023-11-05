package de.tum.cit.ase.api.interfaces;

import de.tum.cit.ase.api.payload.PublishPayload;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController()
public interface PublisherApi {

    @PostMapping(path="/publish",
            consumes = {"application/json"})
    ResponseEntity<?> publish(@RequestBody PublishPayload payload);
}
