package com.example.callback.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "approval_tasks")
public class ApprovalTask {
    
    @Id
    @Column(name = "task_id")
    private String taskId;
    
    @Column(name = "question_id")
    private String questionId;
    
    @Column(name = "assessor_email")
    private String assessorEmail;
    
    @Column(name = "status")
    private String status;
    
    @Column(name = "task_token")
    private String taskToken;
    
    @Column(name = "comments")
    private String comments;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    // Constructors
    public ApprovalTask() {}
    
    public ApprovalTask(String taskId) {
        this.taskId = taskId;
    }
    
    // Getters and Setters
    public String getTaskId() { return taskId; }
    public void setTaskId(String taskId) { this.taskId = taskId; }
    
    public String getQuestionId() { return questionId; }
    public void setQuestionId(String questionId) { this.questionId = questionId; }
    
    public String getAssessorEmail() { return assessorEmail; }
    public void setAssessorEmail(String assessorEmail) { this.assessorEmail = assessorEmail; }
    
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    
    public String getTaskToken() { return taskToken; }
    public void setTaskToken(String taskToken) { this.taskToken = taskToken; }
    
    public String getComments() { return comments; }
    public void setComments(String comments) { this.comments = comments; }
    
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}