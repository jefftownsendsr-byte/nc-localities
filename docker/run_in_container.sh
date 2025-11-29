#!/usr/bin/env bash
OUTPUT_DIR="$(pwd)/output"
IMAGE_NAME="nc-localities:latest"

mkdir -p "$OUTPUT_DIR"
docker build -t "$IMAGE_NAME" ..
docker run --rm -v "$OUTPUT_DIR":/workspace/output "$IMAGE_NAME"

printf "Docker run completed. Check %s for outputs.\n" "$OUTPUT_DIR"
