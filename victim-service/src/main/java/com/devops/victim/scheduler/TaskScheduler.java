package com.devops.victim.scheduler;

import com.devops.victim.algorithms.ArrayStringOps;
import com.devops.victim.algorithms.BinPacking;
import com.devops.victim.algorithms.FacilityLocation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.Random;

/**
 * Periodically executes algorithm tasks, cycling through the available
 * implementations. Some executions will hit intentional bugs, producing
 * realistic ERROR stack traces in the log file.
 */
@Component
public class TaskScheduler {

    private static final Logger log = LoggerFactory.getLogger(TaskScheduler.class);
    private final Random random = new Random();
    private int executionCount = 0;

    private final FacilityLocation facilityLocation = new FacilityLocation();
    private final BinPacking binPacking = new BinPacking();
    private final ArrayStringOps arrayStringOps = new ArrayStringOps();

    /**
     * Runs every 20 seconds. Picks a random algorithm task to execute.
     * Approximately 40% of executions will trigger buggy code paths.
     */
    @Scheduled(fixedRate = 20000, initialDelay = 5000)
    public void runScheduledTask() {
        executionCount++;
        int taskType = random.nextInt(6);

        log.info("===== Execution #{} started | Task type: {} =====", executionCount, taskType);

        try {
            switch (taskType) {
                case 0 -> {
                    log.info("Running Facility Location approximation (normal path)...");
                    facilityLocation.solveNormal();
                    log.info("Facility Location completed successfully.");
                }
                case 1 -> {
                    log.info("Running Facility Location approximation (edge case)...");
                    // This path triggers the NullPointerException bug
                    facilityLocation.solveWithBug();
                    log.info("Facility Location completed successfully.");
                }
                case 2 -> {
                    log.info("Running Bin Packing FFD algorithm (normal path)...");
                    binPacking.solveNormal();
                    log.info("Bin Packing completed successfully.");
                }
                case 3 -> {
                    log.info("Running Bin Packing FFD algorithm (edge case)...");
                    // This path triggers the ArrayIndexOutOfBoundsException bug
                    binPacking.solveWithBug();
                    log.info("Bin Packing completed successfully.");
                }
                case 4 -> {
                    log.info("Running Array/String manipulations (normal path)...");
                    arrayStringOps.processNormal();
                    log.info("Array/String ops completed successfully.");
                }
                case 5 -> {
                    log.info("Running Array/String manipulations (edge case)...");
                    // This path triggers StringIndexOutOfBoundsException + memory leak
                    arrayStringOps.processWithBug();
                    log.info("Array/String ops completed successfully.");
                }
            }
        } catch (Exception e) {
            log.error("CRITICAL FAILURE in execution #{} | Task type: {} | Exception: {}",
                    executionCount, taskType, e.getClass().getSimpleName(), e);
        }

        log.info("===== Execution #{} finished =====", executionCount);
    }

    /**
     * Separate health-check log emitted every 60 seconds.
     */
    @Scheduled(fixedRate = 60000, initialDelay = 10000)
    public void healthCheck() {
        long freeMemory = Runtime.getRuntime().freeMemory() / (1024 * 1024);
        long totalMemory = Runtime.getRuntime().totalMemory() / (1024 * 1024);
        long usedMemory = totalMemory - freeMemory;

        log.info("[HEALTH] Memory usage: {}MB / {}MB | Free: {}MB | Executions so far: {}",
                usedMemory, totalMemory, freeMemory, executionCount);

        if (usedMemory > totalMemory * 0.85) {
            log.warn("[HEALTH] WARNING: Memory usage exceeds 85% threshold! Possible memory leak detected.");
        }
    }
}
