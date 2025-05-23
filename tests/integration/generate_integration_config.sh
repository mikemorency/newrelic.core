#!/bin/sh

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
prefix=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 6)

touch "$SCRIPT_DIR/integration_config.yml"
: > "$SCRIPT_DIR/integration_config.yml"
{
    echo "---"
    echo "integration_config_nr_api_key: '$NR_API_KEY'"
    echo "integration_config_nr_account_id: '$NR_ACCOUNT_ID'"
    echo "integration_config_nr_log_level: '$NR_LOG_LEVEL'"
    echo "test_prefix: 'newrelic-core-$prefix'"
} >> "$SCRIPT_DIR/integration_config.yml"
