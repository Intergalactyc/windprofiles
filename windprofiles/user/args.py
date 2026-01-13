import configparser
import argparse
import json


class CustomParser:
    def __init__(self, config_structure: dict = {}):
        for k, v in config_structure.items():
            if not isinstance(k, str):
                raise TypeError(
                    f"Invalid config structure top-level key {k} (type {type(k)}, must be str)"
                )
            if k in {"args", "tag"}:
                raise ValueError(
                    "Config structure cannot have block (top-level key) named 'args' or 'tag'"
                )
            if not isinstance(v, dict):
                raise TypeError(
                    f"Invalid config structure top-level value corresponding to key {k} (type {type(v)}, must be dict)"
                )
            for kk, vv in v.items():
                if not isinstance(kk, str):
                    raise TypeError(
                        f"Invalid config structure bottom-level key {kk} (type {type(kk)}), must be str"
                    )
                if (
                    not isinstance(vv, tuple)
                    or len(vv) != 3
                    or not isinstance(vv[0], type)
                    or vv[0] not in {str, int, float, list, bool}
                    or not isinstance(vv[1], bool)
                    or not (
                        isinstance(vv[2], vv[0]) or (vv[2] is None and vv[1])
                    )
                ):
                    raise TypeError(
                        f"Invalid config structure bottom-level value corresponding to key {kk} (should be triple (type, required, default) with type in {{str, int, float, list, bool}})"
                    )
        self._config_structure = config_structure
        self.argparser = argparse.ArgumentParser()
        self.argparser.add_argument("config", type=str, metavar="CONFIG_PATH")
        self.cfgparser = configparser.ConfigParser(allow_no_value=False)

    @property
    def _cl_names(self):
        return {
            d for a in self.argparser._actions if (d := a.dest) != "config"
        }

    def add_config_block(self, name: str, overwrite: bool = False):
        if name in self._config_structure and not overwrite:
            raise KeyError(f"Block {name} already exists in config")
        if name in {"args", "tag"}:
            raise ValueError(
                "Config structure cannot have block (top-level key) named 'args' or 'tag'"
            )
        self._config_structure[name] = {}

    def add_config_item(
        self,
        block: str,
        name: str,
        type: type,
        required: bool = False,
        default=None,
        *,
        create_missing_block: bool = True,
        overwrite: bool = False,
    ):
        if block not in self._config_structure:
            if create_missing_block:
                self.add_config_block(block)
            else:
                raise KeyError(f"Block {block} does not exist in config")
        if name in self._config_structure[block] and not overwrite:
            raise KeyError(f"{name} already exists in config block {block}")
        if not required and default is None:
            raise ValueError(
                "For optional (not required) items, `default` must be specified"
            )
        self._config_structure[block][name] = (type, required, default)

    def _parse_cl(self):
        args = self.argparser.parse_args()
        return vars(args)

    def _get_from_parser(self, block, name, _type, required, default):
        _FALLBACK = "!__NONE__!"
        val = self.cfgparser.get(block, name, fallback=_FALLBACK)
        if val == _FALLBACK:
            if required:
                raise ValueError(
                    f"Did not receive required configuration argument {name} in block {block}"
                )
            val = default
        else:
            if _type is list:
                val = json.loads(val)
        val = _type(val)
        if _type is str:
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
        return val

    def _parse_cfg(self, filepath):
        self.cfgparser.read(filepath)
        result = {
            k: {kk: self._get_from_parser(k, kk, *vv) for kk, vv in v.items()}
            for k, v in self._config_structure.items()
        }
        return result

    def add_argument(self, *args, **kwargs):
        self.argparser.add_argument(*args, **kwargs)

    def parse(self):
        result = {}
        args = self._parse_cl()
        config_path = args["config"]
        del args["config"]
        result["args"] = args
        result["tag"] = (
            str(config_path).split("/")[-1].split("\\")[-1].split(".")[0]
        )
        result.update(self._parse_cfg(config_path))
        return result


class Parser:
    # old
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
