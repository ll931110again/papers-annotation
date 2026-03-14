Flink is a framework for stateful computation over streaming data. Flink unifies batch and streaming computation into a unified framework.

To unpack the meaning, we first think about data streams. This corresponds to a number of things, such as stock trade or live feed.

In the Flink framework, one provides source and sink connectors: they can be files or message queues. Flink receives the data and apply internal computations, which then outputs the data to the sink connectors.

The state diagram goes as following:
        source ->   computation   -> sink

Within computation, there's an internal state machine which keeps track of states and applies output accordingly.

Some applications:
* Replication (computation = identity function)
* Accumulation (computation = prefix sum)