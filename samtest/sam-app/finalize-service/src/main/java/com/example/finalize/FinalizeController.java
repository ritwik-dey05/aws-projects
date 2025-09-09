package com.example.finalize;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/finalize")
public class FinalizeController {

    @Autowired
    private FinalizeService finalizeService;

    @PostMapping
    public ResponseEntity<Map<String, Object>> finalize(@RequestBody Map<String, Object> payload) {
        try {
            Map<String, Object> result = finalizeService.finalizeTask(payload);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of(
                "status", "error",
                "message", e.getMessage()
            ));
        }
    }
}