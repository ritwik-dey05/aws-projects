package com.example.callback;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.scheduling.annotation.EnableScheduling;

import com.fasterxml.jackson.databind.ObjectMapper;

@SpringBootApplication
@EnableScheduling
public class CallbackConsumerApplication {
    public static void main(String[] args) {
        SpringApplication.run(CallbackConsumerApplication.class, args);
    }
    
    @Bean
    public ObjectMapper objectMapper() {
    	return new ObjectMapper();
    }
}