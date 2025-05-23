import logging


logger = logging.getLogger(__name__)


class NrObjectBase:
    def __init__(self, name: str, account_id: str):
        self.name = name
        self.account_id = str(account_id)
        self._equality_attrs = set(["name", "account_id"])

    def to_json(self):
        o = {}
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            if hasattr(v, "to_json"):
                o[k] = v.to_json()
                continue

            if isinstance(v, list) or isinstance(v, set):
                o[k] = self.__list_to_json(v)
            elif isinstance(v, dict):
                o[k] = v
            else:
                o[k] = str(v)

        return o

    def __list_to_json(self, l):
        if isinstance(l, set):
            l = list(l)

        o = []
        for val in l:
            try:
                o.append(val.to_json())
            except AttributeError:
                o.append(str(val))
        return o

    def __eq__(self, other):
        if not isinstance(other, NrObjectBase):
            return False

        logger.info("Comparing first: %s", self.to_json())
        logger.info("To second: %s", other.to_json())
        for attr in self._equality_attrs:
            self_val = getattr(self, attr, None)
            other_val = getattr(other, attr, None)
            if isinstance(attr, list):
                self_val, other_val = set(self_val), set(other_val)

            if self_val == other_val:
                continue

            logger.info("%s is different", attr)
            return False

        return True
