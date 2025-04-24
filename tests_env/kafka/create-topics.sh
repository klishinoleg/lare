#!/bin/bash
sleep 10
set -e

BOOTSTRAP_SERVER="kafka:29092"

TOPICS=(
  "chapter.text.processed"
  "chapter.words.saved"
  "chapter.create.requested"
  "chapter.creation.completed"
  "chapter.creation.error"
)

for TOPIC in "${TOPICS[@]}"; do
  echo "🔧 Creating topic: $TOPIC"
  kafka-topics \
    --create \
    --if-not-exists \
    --bootstrap-server "$BOOTSTRAP_SERVER" \
    --replication-factor 1 \
    --partitions 10 \
    --topic "$TOPIC"
done

echo "✅ All topics created or already exist"
