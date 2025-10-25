#!/bin/bash
#
# Test script for fresh Docker container installation
# This simulates pulling and running octofree on Unraid without dev files
#

set -e  # Exit on error

echo "════════════════════════════════════════════════════════════════"
echo "  🐳 FRESH DOCKER CONTAINER TEST"
echo "  Testing octofree as if freshly pulled on Unraid"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Configuration
IMAGE_NAME="octofree-test"
CONTAINER_NAME="octofree-fresh-test"
TEST_OUTPUT_DIR="/tmp/octofree-test-output"

# Clean up any existing test container/image
echo "🧹 Cleaning up any existing test containers..."
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true
docker rmi ${IMAGE_NAME} 2>/dev/null || true

# Clean up test output directory
echo "🧹 Cleaning test output directory..."
rm -rf ${TEST_OUTPUT_DIR}
mkdir -p ${TEST_OUTPUT_DIR}
chmod 777 ${TEST_OUTPUT_DIR}

echo ""
echo "📦 Building Docker image from current code..."
docker build -t ${IMAGE_NAME} .

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  🚀 STARTING FRESH CONTAINER"
echo "  Container name: ${CONTAINER_NAME}"
echo "  Output directory: ${TEST_OUTPUT_DIR}"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Run container in test mode with SINGLE_RUN
# This simulates a fresh installation with no existing files
docker run -d \
  --name ${CONTAINER_NAME} \
  -e DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/TEST/TEST" \
  -e TEST_MODE="false" \
  -e SINGLE_RUN="true" \
  -e OUTPUT_DIR="/data" \
  -v ${TEST_OUTPUT_DIR}:/data \
  ${IMAGE_NAME}

echo "⏳ Waiting for container to complete (SINGLE_RUN mode)..."
echo ""

# Wait for container to finish (max 60 seconds)
for i in {1..60}; do
  if ! docker ps | grep -q ${CONTAINER_NAME}; then
    echo "✅ Container finished execution"
    break
  fi
  echo -n "."
  sleep 1
done
echo ""

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  📋 CONTAINER LOGS"
echo "════════════════════════════════════════════════════════════════"
docker logs ${CONTAINER_NAME}

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  📂 FILES CREATED IN OUTPUT DIRECTORY"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Expected files:"
echo "  - octofree.log"
echo "  - scheduled_sessions.json"
echo "  - past_scheduled_sessions.json"
echo "  - last_sent_session.txt"
echo "  - last_extracted_sessions.json"
echo ""
echo "Actual files created:"
ls -lh ${TEST_OUTPUT_DIR}/ || echo "❌ No files created!"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  🔍 FILE CONTENTS CHECK"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check each expected file
check_file() {
  local file=$1
  local filepath="${TEST_OUTPUT_DIR}/${file}"
  
  if [ -f "${filepath}" ]; then
    echo "✅ ${file} EXISTS"
    echo "   Size: $(stat -f%z "${filepath}" 2>/dev/null || stat -c%s "${filepath}" 2>/dev/null) bytes"
    echo "   Preview:"
    if [ "${file}" == "octofree.log" ]; then
      head -20 "${filepath}" | sed 's/^/   | /'
    else
      cat "${filepath}" | sed 's/^/   | /'
    fi
    echo ""
  else
    echo "❌ ${file} MISSING"
    echo ""
  fi
}

check_file "octofree.log"
check_file "scheduled_sessions.json"
check_file "past_scheduled_sessions.json"
check_file "last_sent_session.txt"
check_file "last_extracted_sessions.json"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  🧪 TEST SUMMARY"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Count created files
FILE_COUNT=$(ls -1 ${TEST_OUTPUT_DIR}/ 2>/dev/null | wc -l | tr -d ' ')
echo "Files created: ${FILE_COUNT} / 5 expected"

if [ ${FILE_COUNT} -ge 5 ]; then
  echo "✅ SUCCESS: All expected files were created"
  EXIT_CODE=0
elif [ ${FILE_COUNT} -gt 0 ]; then
  echo "⚠️  PARTIAL: Some files created but not all"
  EXIT_CODE=1
else
  echo "❌ FAILURE: No output files were created"
  EXIT_CODE=2
fi

echo ""
echo "Container exit code: $(docker inspect ${CONTAINER_NAME} --format='{{.State.ExitCode}}')"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  🧹 CLEANUP OPTIONS"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "To clean up test artifacts, run:"
echo "  docker rm ${CONTAINER_NAME}"
echo "  docker rmi ${IMAGE_NAME}"
echo "  rm -rf ${TEST_OUTPUT_DIR}"
echo ""
echo "Or run this command to clean up everything:"
echo "  docker rm ${CONTAINER_NAME} && docker rmi ${IMAGE_NAME} && rm -rf ${TEST_OUTPUT_DIR}"
echo ""

exit ${EXIT_CODE}
