package com.example.callback.service;

import com.example.callback.entity.ApprovalTask;
import com.example.callback.entity.Question;
import com.example.callback.repository.ApprovalTaskRepository;
import com.example.callback.repository.QuestionRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.DeleteMessageRequest;
import software.amazon.awssdk.services.sqs.model.Message;
import software.amazon.awssdk.services.sqs.model.ReceiveMessageRequest;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
public class SqsMessageProcessor {
    private static final Logger logger = LoggerFactory.getLogger(SqsMessageProcessor.class);
    
    private final SqsClient sqsClient;
    private final ObjectMapper objectMapper;
    private final ApprovalTaskRepository taskRepository;
    private final QuestionRepository questionRepository;
    
    @Value("${sqs.queue.url}")
    private String queueUrl;
    
    @Value("${app.base.url:https://example.com}")
    private String appBaseUrl; 
    
    public SqsMessageProcessor(SqsClient sqsClient, ObjectMapper objectMapper, 
                              ApprovalTaskRepository taskRepository, QuestionRepository questionRepository) {
        this.sqsClient = sqsClient;
        this.objectMapper = objectMapper;
        this.taskRepository = taskRepository;
        this.questionRepository = questionRepository;
    }
    
    @Scheduled(fixedDelay = 5000)
    public void processMessages() {
        try {
            ReceiveMessageRequest request = ReceiveMessageRequest.builder()
                .queueUrl(queueUrl)
                .maxNumberOfMessages(5)
                .waitTimeSeconds(10)
                .build();
                
            List<Message> messages = sqsClient.receiveMessage(request).messages();
            
            for (Message message : messages) {
                try {
                    processMessage(message);
                    deleteMessage(message);
                } catch (Exception e) {
                    logger.error("Failed to process message: {}", message.messageId(), e);
                }
            }
        } catch (Exception e) {
            logger.error("Error processing SQS messages", e);
        }
    }
    
    private void processMessage(Message message) {
        try {
            String body = message.body();
            logger.info("Callback_Consumer:: Received message: {}", body);
            
            CallbackMessage payload = parseMessage(body);
            
            // Update database
            int updated = taskRepository.updateTaskToken(
                payload.getTaskId(), 
                payload.getTaskToken(), 
                LocalDateTime.now()
            );
            
            if (updated > 0) {
                // Get task and question details
                Optional<ApprovalTask> taskOpt = taskRepository.findById(payload.getTaskId());
                if (taskOpt.isPresent()) {
                    ApprovalTask task = taskOpt.get();
                    Optional<Question> questionOpt = questionRepository.findById(task.getQuestionId());
                    
                    String title = questionOpt.map(Question::getTitle).orElse("Approval Request");
                    
                    // Generate approval URLs
                    String approveUrl = String.format("%s/requests/%s/decision?decision=APPROVE", 
                        appBaseUrl, payload.getTaskId());
                    String rejectUrl = String.format("%s/requests/%s/decision?decision=REJECT", 
                        appBaseUrl, payload.getTaskId());
                    
                    String subject = String.format("Approval required: %s", title);
                    String bodyText = String.format(
                        "You have a pending approval task.\\n\\nTask ID: %s\\nTitle: %s\\n\\nApprove: %s\\nReject: %s\\n",
                        payload.getTaskId(), title, approveUrl, rejectUrl
                    );
                    
                    logger.info("Callback_Consumer:: Sending Email: {}", bodyText);
                    // TODO: Implement email sending
                } else {
                	logger.error("No Task Id found.. Returning a warning back to the Approver.. also Aborting the Step function Execution");
                }
            }
            
        } catch (Exception e) {
            logger.error("Error processing message", e);
            throw e;
        }
    }
    
    private CallbackMessage parseMessage(String body) {
        try {
            return objectMapper.readValue(body, CallbackMessage.class);
        } catch (Exception e) {
            try {
                // Try parsing as nested JSON
                String nestedBody = objectMapper.readValue(body, String.class);
                return objectMapper.readValue(nestedBody, CallbackMessage.class);
            } catch (Exception ex) {
                throw new RuntimeException("Failed to parse message: " + body, ex);
            }
        }
    }
    
    private void deleteMessage(Message message) {
        DeleteMessageRequest deleteRequest = DeleteMessageRequest.builder()
            .queueUrl(queueUrl)
            .receiptHandle(message.receiptHandle())
            .build();
        sqsClient.deleteMessage(deleteRequest);
    }
}