import sys
from datetime import datetime

if __name__ == "__main__":
    fname = sys.argv[1]
    f = open(fname, "r")
    summed_used_memory_readouts = [0]
    sum = 0
    job_jvm_heap_used = 0
    job_jvm_nonheap_used = 0
    flink_managed_used = 0
    task_jvm_heap_used = 0
    task_jvm_nonheap_used = 0
    start_datetime = None
    end_datetime = None
    for line in f:
        if "Finished metrics report" in line:
            sum = (
                job_jvm_heap_used
                + job_jvm_nonheap_used
                + flink_managed_used
                + task_jvm_heap_used
                + task_jvm_nonheap_used
            )
            sum_gb = sum / (1024**3)
            summed_used_memory_readouts.append(sum)

            job_jvm_heap_used = 0
            job_jvm_nonheap_used = 0
            flink_managed_used = 0
            task_jvm_heap_used = 0
            task_jvm_nonheap_used = 0
            continue

        if "jobmanager.Status.JVM.Memory.Heap.Used" in line:
            job_jvm_heap_used = int(line.split(" ")[-1])
            continue
        if "jobmanager.Status.JVM.Memory.NonHeap.Used" in line:
            job_jvm_nonheap_used = int(line.split(" ")[-1])
            continue
        if "Status.Flink.Memory.Managed.Used" in line:
            flink_managed_used = int(line.split(" ")[-1])
            continue
        if "Status.JVM.Memory.Heap.Used" in line and ".taskmanager." in line:
            task_jvm_heap_used = int(line.split(" ")[-1])
            continue
        if "Status.JVM.Memory.NonHeap.Used" in line and ".taskmanager." in line:
            task_jvm_nonheap_used = int(line.split(" ")[-1])
            continue

        if "Received JobGraph submission" in line:
            start_datetime = " ".join(line.split(",")[0].split(" ")[-2:])
            start_datetime = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")

        if "reached terminal state FINISHED" in line:
            end_datetime = " ".join(line.split(",")[0].split(" ")[-2:])
            end_datetime = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")

    duration = (end_datetime - start_datetime).seconds
    max_memory = max(summed_used_memory_readouts)
    max_memory_gb = max_memory / (1024**3)
    print(f"{duration} {duration} {max_memory/1024}")
