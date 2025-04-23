#!/bin/bash

if [ "$#" -eq 0 ]; then
  echo "Usage: $0 [-b] [-w] [-m]"
  echo "Options:"
  echo "  -b: Build Tailwind CSS without minification"
  echo "  -w: Run Tailwind CSS in watch mode"
  echo "  -m: Build Tailwind CSS with minification"
  exit 1
fi

while getopts "bmw" flag; do
  case $flag in
    b) npx tailwindcss -i ./src/input.css -o ../homepage/static/tailwindcss.css ;;
    w) npx tailwindcss -i ./src/input.css -o ../homepage/static/tailwindcss.css --watch ;;
    m) npx tailwindcss -i ./src/input.css -o ../homepage/static/tailwindcss.css --minify;;
    *) echo "Invalid option. Use $0 -h for help." ;;
  esac
done
