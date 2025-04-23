#!/bin/bash

while getopts ":b" opt; do
  case $opt in
    b)
		docker rm `docker ps -aq`
		docker rmi dchat_local_django dchat_local_celeryworker dchat_production_mediaserver
		docker compose -f local.yml up
      ;;
    \?)
      # If an invalid option is provided, show a message and exit
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

# If no '-d' flag is given, run the 'ls' command
if [ $OPTIND -eq 1 ]; then
	docker compose -f local.yml up
fi
