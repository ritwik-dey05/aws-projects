package com.example.createrequest;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.UUID;

@RestController
public class CreateRequestController {
    
    @Autowired
    private QuestionRepository questionRepository;
    
    @Autowired
    private ApprovalTaskRepository approvalTaskRepository;
    
    @PostMapping("/create-request")
    public ResponseEntity<Map<String, Object>> createRequest(@RequestBody Map<String, String> request) {
        String title = request.get("title");
        String content = request.get("content");
        String assessorEmail = request.get("assessorEmail");
        
        if (title == null || title.trim().isEmpty() || 
            assessorEmail == null || assessorEmail.trim().isEmpty()) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "title and assessorEmail are required"));
        }
        
        String questionId = UUID.randomUUID().toString();
        String taskId = UUID.randomUUID().toString();
        LocalDateTime now = LocalDateTime.now();
        
        Question question = new Question();
        question.setQuestionId(questionId);
        question.setTitle(title.trim());
        question.setContent(content != null ? content.trim() : "");
        question.setCreatedAt(now);
        questionRepository.save(question);
        
        ApprovalTask task = new ApprovalTask();
        task.setTaskId(taskId);
        task.setQuestionId(questionId);
        task.setAssessorEmail(assessorEmail.trim());
        task.setStatus("PENDING");
        task.setCreatedAt(now);
        task.setUpdatedAt(now);
        approvalTaskRepository.save(task);
        
        return ResponseEntity.ok(Map.of(
            "taskId", taskId,
            "questionId", questionId,
            "assessorEmail", assessorEmail.trim(),
            "title", title.trim()
        ));
    }
}