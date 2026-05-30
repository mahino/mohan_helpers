#!/bin/bash
# Quick setup script for Java TCO Modifier

echo "=========================================="
echo "TCO Modifier - Java Setup Script"
echo "=========================================="
echo ""

# Check Java
echo "Checking Java installation..."
if command -v java &> /dev/null; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2)
    echo "✓ Java found: $JAVA_VERSION"
else
    echo "✗ Java not found"
    echo "  Installing Java 11..."
    sudo yum install -y java-11-openjdk java-11-openjdk-devel
fi

echo ""

# Check Maven
echo "Checking Maven installation..."
if command -v mvn &> /dev/null; then
    MVN_VERSION=$(mvn -version | head -n 1)
    echo "✓ Maven found: $MVN_VERSION"
else
    echo "✗ Maven not found"
    echo "  Installing Maven..."
    sudo yum install -y maven
fi

echo ""

# Create directory
echo "Creating tco_reports directory..."
mkdir -p tco_reports
echo "✓ Directory created"

echo ""

# Build project
echo "Building Java project..."
mvn clean package

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Setup complete!"
    echo "=========================================="
    echo ""
    echo "To run the TCO modifier:"
    echo "  java -jar target/tco-modifier-1.0.0.jar"
    echo ""
    echo "Or use the run script:"
    echo "  ./run_java_modifier.sh"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "✗ Build failed"
    echo "=========================================="
    echo ""
    echo "Please check the error messages above."
    echo "You may need to install dependencies manually."
    exit 1
fi

