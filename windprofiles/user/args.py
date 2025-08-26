import configparser
import argparse


class Parser:
    def __init__(self, paths: list = []):
        self._paths = paths

        self.argparser = argparse.ArgumentParser()
        self.argparser.add_argument("--config", type=str, default="config.ini")

        self.cfgparser = configparser.ConfigParser()

    def _parse_cl(self):
        args = self.argparser.parse_args()
        return vars(args)

    def _parse_cfg(self, filepath):
        self.cfgparser.read(filepath)
        return (
            {p: self.cfgparser.get("paths", p) for p in self._paths}
            if self._paths
            else {}
        )

    def add_argument(self, *args, **kwargs):
        self.argparser.add_argument(*args, **kwargs)

    def parse(self):
        args = self._parse_cl()
        args.update(self._parse_cfg(args["config"]))
        del args["config"]
        return args
