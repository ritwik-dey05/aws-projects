package com.example.finalize;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Service
public class FinalizeService {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    public Map<String, Object> finalizeTask(Map<String, Object> payload) {
        String taskId = (String) payload.get("taskId");
        String decision = (String) payload.getOrDefault("decision", "UNKNOWN");
        String comments = (String) payload.getOrDefault("comments", "");

        if (taskId == null || taskId.isEmpty()) {
            return Map.of("status", "noop");
        }

        Map<String, String> statusMap = Map.of(
            "APPROVE", "APPROVED",
            "REJECT", "REJECTED", 
            "TIMED_OUT", "TIMED_OUT",
            "FAILED", "FAILED"
        );

        String newStatus = statusMap.getOrDefault(decision, decision);

        jdbcTemplate.update(
            "UPDATE approval_tasks SET status=?, comments=?, updated_at=?, task_token=NULL WHERE task_id=?",
            newStatus, comments, LocalDateTime.now(), taskId
        );

        Map<String, Object> result = new HashMap<>();
        result.put("status", "updated");
        result.put("taskId", taskId);
        result.put("statusSet", newStatus);
        
        return result;
    }
}