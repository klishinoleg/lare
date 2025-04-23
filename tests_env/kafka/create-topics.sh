#!/bin/bash
sleep 10

kafka-topics.sh --create --topic chapter.text.processed --bootstrap-server kafka:9092 --replication-factor 1 --partitions 1
kafka-topics.sh --create --topic chapter.words.saved --bootstrap-server kafka:9092 --replication-factor 1 --partitions 1
kafka-topics.sh --create --topic chapter.create.requested --bootstrap-server kafka:9092 --replication-factor 1 --partitions 1
kafka-topics.sh --create --topic chapter.creation.completed --bootstrap-server kafka:9092 --replication-factor 1 --partitions 1
kafka-topics.sh --create --topic chapter.creation.error --bootstrap-server kafka:9092 --replication-factor 1 --partitions 1
