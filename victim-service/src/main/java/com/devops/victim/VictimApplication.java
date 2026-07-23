package com.devops.victim;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Victim Service — a simulated backend worker that runs approximation
 * algorithms and array/string manipulations. Contains intentional bugs
 * that produce realistic stack traces for the AI debugging pipeline.
 */
@SpringBootApplication
@EnableScheduling
public class VictimApplication {

    public static void main(String[] args) {
        SpringApplication.run(VictimApplication.class, args);
    }
}
