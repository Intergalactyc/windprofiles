import configparser
import argparse


class Parser:
    def __init__(
        self, paths: list = [], define: list = [], special: list = []
    ):
        if (
            set(paths) & set(define)
            or set(paths) & set(special)
            or set(define) & set(special)
        ):
            raise ValueError(
                "Cannot have any overlap between `paths`, `define`, `special"
            )

        self._paths = paths
        self._define = define
        self._special = special

        self.argparser = argparse.ArgumentParser()
        self.argparser.add_argument("--config", type=str, default="config.ini")

        self.cfgparser = configparser.ConfigParser(allow_no_value=True)

    def _parse_cl(self):
        args = self.argparser.parse_args()
        return vars(args)

    def _parse_cfg(self, filepath):
        self.cfgparser.read(filepath)
        result = (
            {p: self.cfgparser.get("paths", p) for p in self._paths}
            if self._paths
            else {}
        )
        for s in self._define:
            sub = {k: v for k, v in self.cfgparser.items(s)}
            result[s] = sub
        other_sections = {}
        for s in self.cfgparser.sections():
            if s == "paths" or s in self._define:
                continue
            sub = []
            for k, v in self.cfgparser.items(s):
                if k in self._special:
                    result[k] = v
                else:
                    sub.append(k)
            other_sections[s] = sub
        result["other"] = other_sections
        return result

    def add_argument(self, *args, **kwargs):
        self.argparser.add_argument(*args, **kwargs)

    def parse(self):
        args = self._parse_cl()
        args.update(self._parse_cfg(args["config"]))
        del args["config"]
        return args
