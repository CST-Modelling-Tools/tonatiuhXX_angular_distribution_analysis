#pragma once

#include <vector>
#include <thread>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <optional>

#include "raypathserver.h"
#include "raypathprocessor.h"

template <typename T>
class ParallelProcessor {
public:
    ParallelProcessor(size_t numThreads, size_t batchSize);

    // Process ray paths using a RayPathProcessor
    std::vector<T> processRayPaths(RaypathServer& server, const RayPathProcessor<T>& processor);

private:
    size_t m_numThreads;              // Number of threads
    size_t m_batchSize;               // Batch size for ray paths

    std::queue<std::vector<RayPath>> m_batchQueue; // Shared queue for batches
    std::mutex m_mutex;               // Mutex for thread synchronization
    std::condition_variable m_condition; // Condition variable for synchronization
    bool m_done = false;              // Flag to signal completion

    // Producer task to load ray paths from the server
    void producerTask(RaypathServer& server);

    // Worker task to process batches of ray paths
    void workerTask(const RayPathProcessor<T>& processor, std::vector<T>& results, std::mutex& resultsMutex);
};

template <typename T>
ParallelProcessor<T>::ParallelProcessor(size_t numThreads, size_t batchSize)
    : m_numThreads(numThreads), m_batchSize(batchSize) {}

template <typename T>
std::vector<T> ParallelProcessor<T>::processRayPaths(RaypathServer& server, const RayPathProcessor<T>& processor) {
    std::vector<T> results;
    std::mutex resultsMutex;

    m_done = false;

    // Launch the producer thread
    std::thread producer(&ParallelProcessor::producerTask, this, std::ref(server));

    // Launch worker threads
    std::vector<std::thread> workers;
    for (size_t i = 0; i < m_numThreads; ++i) {
        workers.emplace_back(&ParallelProcessor::workerTask, this, std::cref(processor), std::ref(results), std::ref(resultsMutex));
    }

    // Wait for the producer to finish
    producer.join();

    // Notify workers to finish
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_done = true;
        m_condition.notify_all();
    }

    // Wait for workers to finish
    for (auto& worker : workers) {
        worker.join();
    }

    return results;
}

template <typename T>
void ParallelProcessor<T>::producerTask(RaypathServer& server) {
    while (true) {
        auto batch = server.serveRayPaths(m_batchSize);
        if (batch.empty()) {
            break; // No more data
        }

        {
            std::lock_guard<std::mutex> lock(m_mutex);
            m_batchQueue.push(std::move(batch));
        }
        m_condition.notify_one();
    }
}

template <typename T>
void ParallelProcessor<T>::workerTask(const RayPathProcessor<T>& processor, std::vector<T>& results, std::mutex& resultsMutex) {
    while (true) {
        std::vector<RayPath> batch;

        // Fetch a batch from the queue
        {
            std::unique_lock<std::mutex> lock(m_mutex);
            m_condition.wait(lock, [&]() { return !m_batchQueue.empty() || m_done; });

            if (m_batchQueue.empty() && m_done) {
                break;
            }

            batch = std::move(m_batchQueue.front());
            m_batchQueue.pop();
        }

        // Process the batch
        std::vector<T> localResults;
        for (const auto& rayPath : batch) {
            auto result = processor.processRayPath(rayPath);
            if (result) {
                localResults.push_back(*result);
            }
        }

        // Append local results to global results
        {
            std::lock_guard<std::mutex> lock(resultsMutex);
            results.insert(results.end(), localResults.begin(), localResults.end());
        }
    }
}
