collection_path = "$(HOME)/.ansible/collections/ansible_collections/newrelic/core"
TARGET ?=

.PHONY: install-collection
install-collection:
	ansible-galaxy collection install --force --no-deps .

.PHONY: sanity
sanity: install-collection
	cd $(collection_path); \
	ansible-test sanity --docker default --color yes

.PHONY: units
units: install-collection
	cd $(collection_path); \
	ansible-test units --docker default --color yes

.PHONY: integration
integration: install-collection
	cd $(collection_path); \
	./tests/integration/generate_integration_config.sh; \
	ANSIBLE_ROLES_PATH=./tests/integration/targets \
	ANSIBLE_COLLECTIONS_PATH=$(collection_path)/../.. \
	ansible-test integration --color yes -vvvv $(TARGET)
