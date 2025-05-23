from ansible.errors import AnsibleError
import logging
from xml.etree import ElementTree
from packaging.version import Version
import re

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


logger = logging.getLogger(__name__)


class AgentVersionFeed:
    def __init__(self):
        if not HAS_REQUESTS:
            raise AnsibleError("Missing required 'requests' python package")

    def get_agent_release_feed(self, url):
        """
        Gets an agent release feed XML from a url
        """
        logging.info("Getting agent release feed from %s", url)
        result = requests.get(url=url)
        result.raise_for_status()
        return result.content

    def parse_latest_release_version_from_feed_xml(self, feed_xml):
        try:
            tree = ElementTree.ElementTree(ElementTree.fromstring(feed_xml))
            releases = tree.findall(".//channel//item//title")
        except Exception as e:
            raise AnsibleError(
                "Unexpected XML data structure provided as NR feed XML", e
            )

        release_versions = self.__parse_release_text(releases)
        try:
            release_versions.sort(key=Version, reverse=True)
        except Exception as e:
            raise AnsibleError(
                "Unable to sort release versions, meaning at least one string is not a version",
                e,
            )

        return release_versions[0]

    def __parse_release_text(self, releases):
        release_versions = list()
        for release in releases:
            logger.debug("Parsing text %s for release version", release)
            try:
                _parsed_text = re.search(r"^[\D]+([\d\.]*).*$", release.text)
                logger.debug("Parsed release version %s", _parsed_text)
                release_versions.append(_parsed_text.group(1))
            except Exception as e:
                raise AnsibleError(
                    "Unable to parse '%s' as release version from NR" % release, e
                )
        return release_versions
