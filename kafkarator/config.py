import base64
import pathlib
import tempfile

from pydantic import BaseSettings


# We need to do some extra work here, because the k8s library doesn't do any advanced config handling.
# See also the configure_k8s startup handler in main
# This should probably be solved in the k8s library, in relation to https://github.com/fiaas/k8s/issues/62

class DataOrFile:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, pathlib.Path):
            return cls(path=v)
        if not isinstance(v, str):
            raise TypeError("string required")
        possible_path = pathlib.Path(v).absolute()
        try:
            if possible_path.exists() and possible_path.is_file():
                return cls(path=possible_path)
        except IOError:
            pass
        return cls(data=v)

    def __init__(self, data=None, path=None):
        self._data = data
        self._path = pathlib.Path(path).absolute() if path else None

    @property
    def path(self):
        if not self._path and self._data:
            with tempfile.NamedTemporaryFile(delete=False) as tfile:
                # Assume it's base64 encoded certificates
                d = base64.b64decode(self._data)
                tfile.write(d)
                tfile.flush()
                self._path = pathlib.Path(tfile.name)
        return self._path

    @property
    def data(self):
        if not self._data and self._path:
            try:
                self._data = self._path.read_text("utf-8")
            except IOError:
                pass
        return self._data


class K8sSettings(BaseSettings):
    api_server: str = "https://kubernetes.default.svc.cluster.local"
    api_token: DataOrFile = pathlib.Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
    api_cert: DataOrFile = pathlib.Path("/var/run/secrets/kubernetes.io/serviceaccount/ca.crt")
    client_cert: DataOrFile = ""
    client_key: DataOrFile = ""

    class Config:
        env_prefix = "k8s_"


class LogSettings(BaseSettings):
    format: str = "json"

    class Config:
        env_prefix = "log_"
