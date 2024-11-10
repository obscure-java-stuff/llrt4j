package org.noframework;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import org.junit.jupiter.api.Test;

public class AppTest {
    @Test
    public void testInitialization() {
        Bootstrap classUnderTest = new Bootstrap();
        assertNotNull(classUnderTest, "constructor passes");
    }
}