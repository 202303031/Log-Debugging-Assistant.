package com.devops.victim.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Application configuration for the Victim Service.
 */
@Configuration
@EnableScheduling
public class AppConfig {
    // Spring Boot auto-configuration handles most of the setup.
    // This class exists as an extension point for future configuration beans.
}
