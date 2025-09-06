package com.example.callback.service;

import com.fasterxml.jackson.annotation.JsonProperty;

public class CallbackMessage {
    
    @JsonProperty("taskId")
    private String taskId;
    
    @JsonProperty("assessorEmail")
    private String assessorEmail;
    
    @JsonProperty("title")
    private String title;
    
    @JsonProperty("taskToken")
    private String taskToken;
    
    // Constructors
    public CallbackMessage() {}
    
    // Getters and Setters
    public String getTaskId() { return taskId; }
    public void setTaskId(String taskId) { this.taskId = taskId; }
    
    public String getAssessorEmail() { return assessorEmail; }
    public void setAssessorEmail(String assessorEmail) { this.assessorEmail = assessorEmail; }
    
    public String getTitle() { return title != null ? title : ""; }
    public void setTitle(String title) { this.title = title; }
    
    public String getTaskToken() { return taskToken; }
    public void setTaskToken(String taskToken) { this.taskToken = taskToken; }
}