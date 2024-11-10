package org.noframework;

import java.io.IOException;
import java.io.OutputStream;

public class Handler {

    public void handle(byte[] request, OutputStream os) throws IOException {
        try {

            // important: the response must be valid json
            String response = String.format("{\"hello\": \"world\", \"request\": \"%s\"}", new String(request));
            os.write(response.getBytes());
        } catch (IOException e) {
            e.printStackTrace(System.err);
        }
    }
}
