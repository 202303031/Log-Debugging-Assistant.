package com.devops.victim.algorithms;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

/**
 * First-Fit Decreasing Bin Packing Approximation Algorithm.
 *
 * Given a list of item sizes and a bin capacity, this algorithm sorts
 * items in decreasing order and places each item into the first bin
 * that has enough remaining capacity.
 *
 * INTENTIONAL BUG: The buggy path has an off-by-one error in the
 * bin remaining capacity array, causing an ArrayIndexOutOfBoundsException
 * when all initial bins are full and a new bin must be opened.
 */
public class BinPacking {

    private static final Logger log = LoggerFactory.getLogger(BinPacking.class);

    /**
     * Normal execution path — works correctly.
     */
    public int solveNormal() {
        double binCapacity = 10.0;
        double[] items = {6.5, 5.0, 4.2, 3.8, 3.5, 2.1, 1.9, 1.5, 1.0, 0.8};

        log.info("Bin Packing: {} items, bin capacity: {}", items.length, binCapacity);

        // Sort descending
        Arrays.sort(items);
        reverseArray(items);

        int maxBins = items.length;
        double[] binRemaining = new double[maxBins];
        int binsUsed = 0;

        for (double item : items) {
            boolean placed = false;
            for (int b = 0; b < binsUsed; b++) {
                if (binRemaining[b] >= item) {
                    binRemaining[b] -= item;
                    placed = true;
                    log.debug("Placed item {:.1f} in bin {} (remaining: {:.1f})", item, b, binRemaining[b]);
                    break;
                }
            }
            if (!placed) {
                binRemaining[binsUsed] = binCapacity - item;
                log.debug("Opened bin {} for item {:.1f} (remaining: {:.1f})", binsUsed, item, binRemaining[binsUsed]);
                binsUsed++;
            }
        }

        log.info("Bin Packing solved | Bins used: {} for {} items", binsUsed, items.length);
        return binsUsed;
    }

    /**
     * Buggy execution path.
     *
     * BUG: The bin remaining capacity array is allocated with size (items.length / 2)
     * instead of items.length. When items are large and don't share bins, the
     * algorithm runs out of array space and throws ArrayIndexOutOfBoundsException.
     */
    public int solveWithBug() {
        double binCapacity = 10.0;
        // Crafted input: many large items that each need their own bin
        double[] items = {9.5, 9.2, 8.8, 8.5, 8.1, 7.9, 7.5, 7.0, 6.8, 6.5, 6.2, 5.9};

        log.info("Bin Packing (edge case): {} items, bin capacity: {}", items.length, binCapacity);

        // Sort descending
        Arrays.sort(items);
        reverseArray(items);

        // BUG: array too small — only half the bins we might need
        int maxBins = items.length / 2;  // Should be items.length!
        double[] binRemaining = new double[maxBins];
        int binsUsed = 0;

        for (int i = 0; i < items.length; i++) {
            double item = items[i];
            boolean placed = false;

            for (int b = 0; b < binsUsed; b++) {
                if (binRemaining[b] >= item) {
                    binRemaining[b] -= item;
                    placed = true;
                    break;
                }
            }

            if (!placed) {
                // BUG TRIGGER: when binsUsed >= maxBins, this throws
                // ArrayIndexOutOfBoundsException
                binRemaining[binsUsed] = binCapacity - item;
                log.debug("Opened bin {} for item {} (remaining: {})", binsUsed, item, binRemaining[binsUsed]);
                binsUsed++;
            }
        }

        log.info("Bin Packing solved | Bins used: {}", binsUsed);
        return binsUsed;
    }

    /**
     * Reverses a double array in-place.
     */
    private void reverseArray(double[] arr) {
        for (int i = 0, j = arr.length - 1; i < j; i++, j--) {
            double temp = arr[i];
            arr[i] = arr[j];
            arr[j] = temp;
        }
    }
}
