#!/bin/bash
# Run the Java TCO Modifier

echo "=========================================="
echo "Running TCO Modifier (Java)"
echo "=========================================="
echo ""

# Check if JAR exists
if [ ! -f "target/tco-modifier-1.0.0.jar" ]; then
    echo "✗ JAR file not found!"
    echo "  Please run: ./setup_java.sh first"
    exit 1
fi

# Run the modifier
java -jar target/tco-modifier-1.0.0.jar

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="

