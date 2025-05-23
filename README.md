# Ansible Collection: newrelic.core

This repo hosts the `newrelic.core` Ansible Collection.

**Note**: This collection is maintained as a personal project. I do not offer any garuntees about updates, features, or bug fixes. I work on this in my spare time and out of casual interest. Please feel free to open issues or PRs though. I will continue to check in and respond.

This collection provides Ansible modules and utils to interact with the New Relic API. For example, users can use the modules to manage alert conditions, policies, and synthetic monitors.

## Requirements

The host running the tasks must have the python requirements described in `requirements.txt`
Once the collection is installed, you can install them into a python environment using pip: `pip install -r ~/.ansible/collections/ansible_collections/newrelic/core/requirements.txt`

### Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.17.0**.

## Installation

Before using this collection, you need to install it with the Ansible Galaxy command-line tool:

```sh
ansible-galaxy collection install https://github.com/mikemorency/newrelic.core.git
```

## Usage

The `tests/integration/targets/*/tasks/main.yml` files have examples of how to use the modules. The modules have documentation inside the python files themsevles too. Feel free to ask questions if needed.

## Testing

All releases will meet the following test criteria.

* 100% success for [Integration](https://github.com/mikemorency/newrelic.core/blob/main/tests/integration) tests.
* 100% success for [Unit](https://github.com/mikemorency/newrelic.core/blob/main/tests/unit) tests.
* 100% success for [Sanity](https://docs.ansible.com/ansible/latest/dev_guide/testing/sanity/index.html#all-sanity-tests) tests as part of [ansible-test](https://docs.ansible.com/ansible/latest/dev_guide/testing.html#run-sanity-tests).
* 100% success for [ansible-lint](https://ansible.readthedocs.io/projects/lint/) allowing only false positives.


## License Information

GNU General Public License v3.0 or later
See [LICENSE](https://github.com/mikemorency/newrelic.core/blob/main/LICENSE) to see the full text.
