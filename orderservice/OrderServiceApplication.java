package com.example.orderservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.http.ResponseEntity;
import org.springframework.http.MediaType;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@SpringBootApplication
@RestController
public class OrderServiceApplication {

    @GetMapping(path = "/order", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String, Object>> getOrder() {
        Map<String, Object> orderResponse = new HashMap<>();
        orderResponse.put("orderId", "ORDER-12345");
        orderResponse.put("customerName", "John Doe");
        orderResponse.put("productName", "Spring Boot Microservice");
        orderResponse.put("quantity", 1);
        orderResponse.put("price", 99.99);
        orderResponse.put("status", "COMPLETED");
        orderResponse.put("orderDate", LocalDateTime.now().toString());
        orderResponse.put("message", "Order retrieved successfully from ECS Fargate service");

        return ResponseEntity.ok(orderResponse);
    }

    public static void main(String[] args) {
        SpringApplication.run(OrderServiceApplication.class, args);
    }
}