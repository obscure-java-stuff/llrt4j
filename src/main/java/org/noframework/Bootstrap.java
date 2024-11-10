package org.noframework;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URISyntaxException;

public class Bootstrap {

    final static String API_URL = "http://" + System.getenv("AWS_LAMBDA_RUNTIME_API") + "/2018-06-01";

    final static Handler handler = new Handler();

    public static void main(String[] args) throws IOException, URISyntaxException {
        for (;;) {
            HttpURLConnection conn = (HttpURLConnection) new URI(API_URL + "/runtime/invocation/next").toURL()
                    .openConnection();
            conn.connect();
            byte[] request;

            try (InputStream is = conn.getInputStream()) {
                request = is.readAllBytes();
            }

            HttpURLConnection http = (HttpURLConnection) new URI(API_URL + "/runtime/invocation/"
                    + conn.getHeaderField("Lambda-Runtime-Aws-Request-Id") + "/response").toURL().openConnection();
            http.setRequestMethod("POST");
            http.setDoOutput(true);
            http.connect();

            try (OutputStream os = http.getOutputStream()) {
                handler.handle(request, os);
            }
            if (http.getResponseCode() >= 300) {
                throw new IllegalStateException("ERROR: statusCode = " + http.getResponseCode());
            }
            http.disconnect();
            conn.disconnect();
        }
    }
}
