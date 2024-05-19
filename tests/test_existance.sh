#!/bin/bash

aws ecr describe-images --repository-name "$1" >/dev/null 2>&1
exit_code=$?

if [[ $exit_code -ne 0 ]]; then
	echo "test failed: ecr repository existance"
	exit $exit_code
else
	echo "test passed: ecr repository existance"
	exit 0
fi
