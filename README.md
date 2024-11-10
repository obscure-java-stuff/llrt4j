Java cold-start optimization experiment.

The goal was to measure the impact of deploying an extremelly small jar, without native AOT or snapstart.

Cold start timing reduced to 400ms by supplying a custom runtime without any dependencies, and deploying only a 4kb jar file inside a 1200-byte Docker image layer.

Not too bad, but still slower than virtually any other option (Python, Node, Go, Rust).
