package com.devops.victim.algorithms;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

/**
 * Greedy Facility Location Approximation Algorithm.
 *
 * Given a set of potential facility locations with opening costs and
 * client-facility connection costs, this algorithm greedily selects
 * facilities to minimize total cost.
 *
 * INTENTIONAL BUG: The buggy path fails to populate the cost map for
 * certain facility IDs, causing a NullPointerException when the
 * algorithm tries to unbox a null Double from the map lookup.
 */
public class FacilityLocation {

    private static final Logger log = LoggerFactory.getLogger(FacilityLocation.class);

    /**
     * Normal execution path — works correctly.
     */
    public Map<Integer, List<Integer>> solveNormal() {
        int numFacilities = 5;
        int numClients = 12;

        // Facility opening costs
        Map<Integer, Double> openingCosts = new HashMap<>();
        for (int i = 0; i < numFacilities; i++) {
            openingCosts.put(i, 10.0 + i * 5.0);
        }

        // Connection costs: client -> facility -> cost
        double[][] connectionCosts = generateConnectionCosts(numClients, numFacilities);

        log.info("Facility Location: {} facilities, {} clients", numFacilities, numClients);

        // Greedy assignment
        Map<Integer, List<Integer>> assignments = new HashMap<>();
        Set<Integer> openedFacilities = new HashSet<>();

        for (int client = 0; client < numClients; client++) {
            double bestCost = Double.MAX_VALUE;
            int bestFacility = -1;

            for (int facility = 0; facility < numFacilities; facility++) {
                double totalCost = connectionCosts[client][facility];
                if (!openedFacilities.contains(facility)) {
                    totalCost += openingCosts.get(facility);
                }
                if (totalCost < bestCost) {
                    bestCost = totalCost;
                    bestFacility = facility;
                }
            }

            openedFacilities.add(bestFacility);
            assignments.computeIfAbsent(bestFacility, k -> new ArrayList<>()).add(client);
            log.debug("Client {} assigned to Facility {} (cost: {:.2f})", client, bestFacility, bestCost);
        }

        double totalCost = calculateTotalCost(assignments, openingCosts, connectionCosts, openedFacilities);
        log.info("Facility Location solved | Opened: {} | Total cost: {}", openedFacilities.size(), totalCost);

        return assignments;
    }

    /**
     * Buggy execution path.
     *
     * BUG: The opening costs map is populated for facilities 0..numFacilities-1,
     * but the algorithm iterates over facility IDs 1..numFacilities (off-by-one).
     * When facility == numFacilities, openingCosts.get(facility) returns null,
     * and the auto-unboxing to double throws a NullPointerException.
     */
    public Map<Integer, List<Integer>> solveWithBug() {
        int numFacilities = 5;
        int numClients = 15;

        // Facility opening costs — populated for IDs 0 through 4
        Map<Integer, Double> openingCosts = new HashMap<>();
        for (int i = 0; i < numFacilities; i++) {
            openingCosts.put(i, 10.0 + i * 5.0);
        }

        double[][] connectionCosts = generateConnectionCosts(numClients, numFacilities);

        log.info("Facility Location (edge case): {} facilities, {} clients", numFacilities, numClients);

        Map<Integer, List<Integer>> assignments = new HashMap<>();
        Set<Integer> openedFacilities = new HashSet<>();

        for (int client = 0; client < numClients; client++) {
            double bestCost = Double.MAX_VALUE;
            int bestFacility = -1;

            // BUG: iterates 1..numFacilities instead of 0..numFacilities-1
            // When facility == numFacilities (5), openingCosts.get(5) returns null
            for (int facility = 1; facility <= numFacilities; facility++) {
                double connectionCost = connectionCosts[client][facility % numFacilities];

                // BUG TRIGGER: openingCosts.get(numFacilities) returns null
                // Auto-unboxing null Double to double throws NullPointerException
                double facilityCost = openingCosts.get(facility);  // NPE when facility == 5!

                double totalCost = connectionCost + (openedFacilities.contains(facility) ? 0 : facilityCost);

                if (totalCost < bestCost) {
                    bestCost = totalCost;
                    bestFacility = facility;
                }
            }

            openedFacilities.add(bestFacility);
            assignments.computeIfAbsent(bestFacility, k -> new ArrayList<>()).add(client);
        }

        log.info("Facility Location solved | Opened: {} facilities", openedFacilities.size());
        return assignments;
    }

    private double[][] generateConnectionCosts(int clients, int facilities) {
        Random rng = new Random(42);
        double[][] costs = new double[clients][facilities];
        for (int i = 0; i < clients; i++) {
            for (int j = 0; j < facilities; j++) {
                costs[i][j] = 1.0 + rng.nextDouble() * 20.0;
            }
        }
        return costs;
    }

    private double calculateTotalCost(Map<Integer, List<Integer>> assignments,
                                       Map<Integer, Double> openingCosts,
                                       double[][] connectionCosts,
                                       Set<Integer> opened) {
        double total = 0;
        for (int fac : opened) {
            total += openingCosts.getOrDefault(fac, 0.0);
            if (assignments.containsKey(fac)) {
                for (int client : assignments.get(fac)) {
                    total += connectionCosts[client][fac];
                }
            }
        }
        return total;
    }
}
