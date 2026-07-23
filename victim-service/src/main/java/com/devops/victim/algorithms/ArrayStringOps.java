package com.devops.victim.algorithms;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

/**
 * Complex Array and String Manipulation Operations.
 *
 * Performs sorting, merging, reversal, palindrome checking, and
 * substring extraction on various data structures.
 *
 * INTENTIONAL BUGS:
 * 1. StringIndexOutOfBoundsException: The palindrome checker fails
 *    when an empty string is included in the input array.
 * 2. Memory Leak: A static list accumulates processed results on
 *    every invocation and is never cleared, growing without bound.
 */
public class ArrayStringOps {

    private static final Logger log = LoggerFactory.getLogger(ArrayStringOps.class);

    /**
     * MEMORY LEAK: This static list grows on every call to processWithBug()
     * and is never cleared. Over time, this will consume increasing heap memory.
     */
    private static final List<String> processedResultsCache = new ArrayList<>();

    /**
     * Normal execution path — works correctly.
     */
    public void processNormal() {
        log.info("Starting normal array/string operations...");

        // 1. Merge and sort two integer arrays
        int[] arr1 = {34, 12, 78, 5, 23, 67, 1};
        int[] arr2 = {89, 45, 11, 56, 99, 3, 42};
        int[] merged = mergeAndSort(arr1, arr2);
        log.info("Merged & sorted {} elements: [{}, ..., {}]",
                merged.length, merged[0], merged[merged.length - 1]);

        // 2. Reverse strings
        String[] words = {"algorithm", "debugging", "container", "pipeline", "orchestration"};
        String[] reversed = reverseStrings(words);
        log.info("Reversed {} words, first: '{}' -> '{}'", words.length, words[0], reversed[0]);

        // 3. Check palindromes
        String[] candidates = {"racecar", "hello", "level", "world", "madam", "kayak"};
        int palindromeCount = countPalindromes(candidates);
        log.info("Found {} palindromes out of {} candidates", palindromeCount, candidates.length);

        // 4. Extract longest common prefix
        String[] strings = {"infrastructure", "infraction", "information", "inflection"};
        String lcp = longestCommonPrefix(strings);
        log.info("Longest common prefix: '{}'", lcp);

        log.info("Normal array/string operations completed successfully.");
    }

    /**
     * Buggy execution path.
     *
     * BUG 1: Includes an empty string "" in the palindrome candidates,
     *         which causes StringIndexOutOfBoundsException in the
     *         palindrome checker (it accesses charAt(0) without length check).
     *
     * BUG 2: Appends results to the static processedResultsCache list
     *         on every invocation, causing a memory leak.
     */
    public void processWithBug() {
        log.info("Starting edge-case array/string operations...");

        // Memory leak: accumulate results into the static cache
        for (int i = 0; i < 1000; i++) {
            processedResultsCache.add("result-entry-" + UUID.randomUUID().toString() +
                    "-" + System.nanoTime());
        }
        log.info("Processed results cache size: {} entries (growing...)", processedResultsCache.size());

        // 1. Merge with potential duplicates
        int[] arr1 = {100, 50, 25, 75, 50, 25};
        int[] arr2 = {60, 30, 90, 120, 30, 60};
        int[] merged = mergeAndSort(arr1, arr2);
        log.info("Merged with duplicates: {} elements", merged.length);

        // 2. Reverse strings including edge cases
        String[] words = {"microservice", "kubernetes", "a", "monitoring"};
        String[] reversed = reverseStrings(words);
        log.info("Reversed {} words successfully", reversed.length);

        // 3. BUG TRIGGER: empty string in candidates causes
        //    StringIndexOutOfBoundsException in buggyPalindromeCheck
        String[] candidates = {"racecar", "deploy", "", "level", "noon", "test"};
        log.info("Checking {} palindrome candidates (including edge cases)...", candidates.length);
        int count = countPalindromesBuggy(candidates);
        log.info("Found {} palindromes", count);

        log.info("Edge-case array/string operations completed.");
    }

    // ======================== Helper Methods ========================

    private int[] mergeAndSort(int[] a, int[] b) {
        int[] result = new int[a.length + b.length];
        System.arraycopy(a, 0, result, 0, a.length);
        System.arraycopy(b, 0, result, a.length, b.length);
        Arrays.sort(result);
        return result;
    }

    private String[] reverseStrings(String[] input) {
        String[] result = new String[input.length];
        for (int i = 0; i < input.length; i++) {
            result[i] = new StringBuilder(input[i]).reverse().toString();
        }
        return result;
    }

    /**
     * Correct palindrome check — handles edge cases.
     */
    private int countPalindromes(String[] candidates) {
        int count = 0;
        for (String s : candidates) {
            if (s != null && !s.isEmpty() && isPalindrome(s)) {
                count++;
            }
        }
        return count;
    }

    /**
     * BUGGY palindrome check — crashes on empty strings.
     *
     * BUG: Accesses s.charAt(0) and s.charAt(s.length()-1) without
     * checking if the string is empty. When s is "", s.length() is 0,
     * and charAt(0) throws StringIndexOutOfBoundsException.
     */
    private int countPalindromesBuggy(String[] candidates) {
        int count = 0;
        for (String s : candidates) {
            // No null/empty check — will crash on ""
            char first = s.charAt(0);     // BUG: throws on empty string!
            char last = s.charAt(s.length() - 1);

            // Quick check: if first and last chars match, do full check
            if (first == last && isPalindrome(s)) {
                count++;
                log.debug("'{}' is a palindrome", s);
            }
        }
        return count;
    }

    private boolean isPalindrome(String s) {
        int left = 0, right = s.length() - 1;
        while (left < right) {
            if (s.charAt(left) != s.charAt(right)) return false;
            left++;
            right--;
        }
        return true;
    }

    private String longestCommonPrefix(String[] strs) {
        if (strs == null || strs.length == 0) return "";
        String prefix = strs[0];
        for (int i = 1; i < strs.length; i++) {
            while (strs[i].indexOf(prefix) != 0) {
                prefix = prefix.substring(0, prefix.length() - 1);
                if (prefix.isEmpty()) return "";
            }
        }
        return prefix;
    }
}
