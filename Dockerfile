# Build stage
FROM public.ecr.aws/amazoncorretto/amazoncorretto:21 AS builder
RUN yum install -y maven
WORKDIR /build

# Cache and copy dependencies
COPY pom.xml .
RUN mvn dependency:go-offline 

# Compile the function
COPY src src
RUN mvn package

# Final stage
FROM public.ecr.aws/amazoncorretto/amazoncorretto:21
WORKDIR /function

# Copy only main application jar and CDS archive
COPY --from=builder /build/target/sample-app-1.jar ./

ENV JAVA_TOOL_OPTIONS="\
    -XX:+TieredCompilation \
    -XX:TieredStopAtLevel=1 \
    -XX:+UseSerialGC \
    -Xms2048m \
    -Xmx2048m \
    -XX:+UseCompressedOops \
    -XX:+UseCompressedClassPointers \
    -Djava.security.egd=file:/dev/urandom \
    -Dfile.encoding=UTF-8"
    
# Main entrypoint
ENTRYPOINT ["java", "-cp", "sample-app-1.jar", "org.noframework.Bootstrap"]