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
	ANSIBLE_ROLES_PATH="./tests/integration/targets/" ansible-test integration --docker default --color yes --verbose $(TARGET)
