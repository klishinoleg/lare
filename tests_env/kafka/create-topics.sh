#!/bin/bash
set -e

BOOTSTRAP_SERVER=${BOOTSTRAP_SERVER:-kafka:29092}
TOPIC_CONFIG=${TOPIC_CONFIG:-/topics/topics.conf}

echo "🔧 Creating topics from $TOPIC_CONFIG"

while IFS='=' read -r TOPIC PARTITIONS || [[ -n "$TOPIC" ]]; do
  TOPIC=$(echo "$TOPIC" | tr -d '[:space:]')
  PARTITIONS=$(echo "$PARTITIONS" | tr -d '[:space:]')
  if [[ -z "$TOPIC" || "$TOPIC" == \#* ]]; then
    continue
  fi
  echo "➡️ Creating topic '$TOPIC' with $PARTITIONS partitions"
  kafka-topics \
    --create \
    --if-not-exists \
    --bootstrap-server "$BOOTSTRAP_SERVER" \
    --replication-factor 1 \
    --partitions "$PARTITIONS" \
    --topic "$TOPIC"
done < "$TOPIC_CONFIG"
echo "✅ Topic creation finished"
