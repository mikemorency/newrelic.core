import logging
import json
import re
import time
import random

MISSING_IMPORTS = set()
try:
    import requests
except ImportError:
    MISSING_IMPORTS.add("requests")

try:
    from jinja2 import Environment
    from jinja2 import BaseLoader
except ImportError:
    MISSING_IMPORTS.add("jinja2")


logger = logging.getLogger(__name__)


class NerdGraphApiBase:
    def __init__(
        self,
        api_key: str,
        wait_for_propegation: bool = True,
        propegation_timeout: int = 10,
    ):
        if MISSING_IMPORTS:
            raise Exception(
                "Missing required python package(s): %s" % ", ".join(MISSING_IMPORTS)
            )
        self.default_headers = {"Api-Key": api_key}
        self.api_base_url = "https://api.newrelic.com/graphql"
        self.jinja_env = Environment(loader=BaseLoader)
        self.wait_for_propegation = wait_for_propegation
        self.propegation_timeout = propegation_timeout

    def run_query(self, query: str):
        try:
            r = requests.post(
                url=self.api_base_url,
                headers=dict(
                    self.default_headers, **{"Content-type": "application/json"}
                ),
                data=json.dumps({"query": query}),
            )
            self.handle_query_errors(r, query)
        except NerdGraphRateLimitError as e:
            logger.warning("%s", e)
            x = random.randrange(0, 15, 1)
            logger.info("Retrying in %s seconds", x)
            time.sleep(x)
            r = requests.post(
                url=self.api_base_url,
                headers=dict(
                    self.default_headers, **{"Content-type": "application/json"}
                ),
                data=json.dumps({"query": query}),
            )
            self.handle_query_errors(r, query)

        return r.json()

    def handle_query_errors(self, response, query):
        response.raise_for_status()
        response = response.json()
        errors = response.get("errors", [])
        if not errors:
            return

        if len(errors) > 1:
            logger.fatal("errors=%s", errors)
            raise Exception("check nerdgraph_client.py")

        if errors[0].get("description", "").startswith("Rate limit exceeded"):
            raise NerdGraphRateLimitError(errors[0])

        if errors[0].get("message", "").startswith("Validation Error"):
            raise NerdGraphValidationError(response, query)

        raise NerdGraphQueryError(response, query)


class NerdGraphQueryError(Exception):
    def __init__(self, response, query, msg: str = None):
        if not msg:
            msg = "An error was returned while executing a query"
        super().__init__(msg)
        self.response = response
        self.query = re.sub(" +", " ", query)
        self.query = re.sub("\n", "", self.query)

    def to_json(self):
        return {
            "response": self.response,
            "query": self.query,
        }


class NerdGraphValidationError(NerdGraphQueryError):
    def __init__(self, response, query):
        super().__init__(
            response, query, msg="There was a validation error with a query."
        )
        self.errors = []
        for error in response["errors"]:
            for val_err in error["extensions"]["validationErrors"]:
                self.errors.append(val_err["reason"])

    def to_json(self):
        return {"errors": self.errors}


class NerdGraphRateLimitError(Exception):
    def __init__(self, error):
        super().__init__(error)
