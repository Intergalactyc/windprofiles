import configparser
import argparse


class Parser:
    def __init__(self, paths: list = [], define: list = []):
        if set(paths) & set(define):
            raise ValueError(
                "Cannot have overlap between `paths` and `define`"
            )

        self._paths = paths
        self._define = define

        self.argparser = argparse.ArgumentParser()
        self.argparser.add_argument("--config", type=str, default="config.ini")

        self.cfgparser = configparser.ConfigParser()

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
        return result

    def add_argument(self, *args, **kwargs):
        self.argparser.add_argument(*args, **kwargs)

    def parse(self):
        args = self._parse_cl()
        args.update(self._parse_cfg(args["config"]))
        del args["config"]
        return args
